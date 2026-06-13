import streamlit as st
import bcrypt
import ssl
import certifi
from pymongo import MongoClient, errors
from pymongo.server_api import ServerApi
import pandas as pd
from datetime import datetime
import json
import os

import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = st.secrets.get("mongo", {}).get("uri", "") or os.environ.get("MONGO_URI", "")

LOCAL_DIR = os.path.join(os.path.dirname(__file__), ".local_db")
os.makedirs(LOCAL_DIR, exist_ok=True)

# ── MongoDB Connection ──

@st.cache_resource
def get_client():
    client = MongoClient(
        MONGO_URI,
        server_api=ServerApi("1"),
        tls=True,
        tlsInsecure=True,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000,
        serverSelectionTimeoutMS=10000,
    )
    return client

def db_available():
    try:
        client = get_client()
        client.admin.command("ping")
        return True
    except Exception:
        return False

def get_db():
    client = get_client()
    return client["kayfa_analytics"]

# ── Local JSON fallback ──

def _local_path(username):
    safe = username.replace(".", "_").replace("@", "_")
    return os.path.join(LOCAL_DIR, f"{safe}.json")

def _load_local(username):
    path = _local_path(username)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"users": {}, "snapshots": {}}

def _save_local(username, data):
    path = _local_path(username)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)

# ── User Auth (MongoDB with JSON fallback) ──

def register_user(username, password):
    if db_available():
        try:
            db = get_db()
            if db.users.find_one({"username": username}):
                return False, "Username already exists"
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            db.users.insert_one({
                "username": username,
                "password": hashed,
                "created_at": datetime.utcnow(),
            })
            return True, "Registration successful (MongoDB)"
        except Exception as e:
            st.warning(f"MongoDB write failed, falling back to local storage: {e}")

    local = _load_local("_system")
    if username in local["users"]:
        return False, "Username already exists"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    local["users"][username] = {
        "password": hashed.decode(),
        "created_at": str(datetime.utcnow()),
    }
    _save_local("_system", local)
    return True, "Registration successful (local storage)"

def authenticate_user(username, password):
    if db_available():
        try:
            db = get_db()
            user = db.users.find_one({"username": username})
            if not user:
                return False, "Invalid username or password"
            if bcrypt.checkpw(password.encode(), user["password"]):
                return True, "Login successful"
            return False, "Invalid username or password"
        except Exception:
            pass

    local = _load_local("_system")
    user = local["users"].get(username)
    if not user:
        return False, "Invalid username or password"
    if bcrypt.checkpw(password.encode(), user["password"].encode()):
        return True, "Login successful"
    return False, "Invalid username or password"

# ── Session State Helpers ──

def require_auth():
    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        st.warning("Please log in first from the Login page.")
        st.stop()

def logout():
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""
    st.rerun()

# ── Save / Load Analysis Results ──

def save_collection(collection_name, data_dict, username=None):
    username = username or st.session_state.get("username", "anonymous")
    record = {
        "data": data_dict,
        "username": username,
        "saved_at": str(datetime.utcnow()),
    }
    if db_available():
        try:
            db = get_db()
            result = db[collection_name].insert_one(record)
            return result.inserted_id
        except Exception:
            pass

    local = _load_local(username)
    if collection_name not in local["snapshots"]:
        local["snapshots"][collection_name] = []
    local["snapshots"][collection_name].append(record)
    _save_local(username, local)
    return str(hash(str(record)))

def load_collections(collection_name, username=None):
    username = username or st.session_state.get("username", "anonymous")
    if db_available():
        try:
            db = get_db()
            cursor = db[collection_name].find({"username": username}).sort("saved_at", -1)
            return list(cursor)
        except Exception:
            pass

    local = _load_local(username)
    snaps = local["snapshots"].get(collection_name, [])
    return sorted(snaps, key=lambda x: x.get("saved_at", ""), reverse=True)

def dataframe_to_dict(df):
    return json.loads(df.to_json(orient="split"))

def dict_to_dataframe(d):
    return pd.read_json(json.dumps(d), orient="split")

# ── Reusable Save UI ──

def render_save_ui(collection_name, data_label, data_dict):
    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        return
    with st.sidebar:
        st.divider()
        if not db_available():
            st.caption("💾 Saving locally (MongoDB unreachable)")
        else:
            st.markdown("**💾 Save to MongoDB**")
        save_name = st.text_input("Snapshot label", key=f"save_name_{collection_name}",
                                  placeholder="e.g. Dec 2025 snapshot")
        if st.button(f"Save {data_label}", key=f"save_btn_{collection_name}"):
            if not save_name.strip():
                st.error("Enter a label")
            else:
                payload = {"label": save_name.strip(), "data": data_dict}
                oid = save_collection(collection_name, payload)
                st.success(f"Saved as '{save_name}'")

        st.markdown("**📂 Load saved snapshots**")
        snapshots = load_collections(collection_name, st.session_state["username"])
        if snapshots:
            labels = [s["data"]["label"] for s in snapshots if "label" in s.get("data", {})]
            if labels:
                selected = st.selectbox("Choose snapshot", labels, key=f"load_sel_{collection_name}")
                if st.button("Load", key=f"load_btn_{collection_name}"):
                    for s in snapshots:
                        if s["data"].get("label") == selected:
                            st.session_state[f"loaded_{collection_name}"] = s["data"]["data"]
                            st.success(f"Loaded '{selected}'")
                            st.rerun()
            else:
                st.caption("No named snapshots yet")
        else:
            st.caption("No saved snapshots yet")
