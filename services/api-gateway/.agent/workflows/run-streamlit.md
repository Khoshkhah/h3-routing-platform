---
description: Start the Streamlit web application for the routing pipeline
---
# Running the Full Routing Stack

This workflow starts all three services needed for the routing application.

// turbo-all

## 1. Start the C++ Routing Server
```bash
cd /home/kaveh/projects/routing-server && ./scripts/run.sh
```

## 2. Start the Python API Gateway
```bash
cd /home/kaveh/projects/routing-pipeline/scripts && ./start_api.sh
```

## 3. Start the Streamlit Web App
```bash
cd /home/kaveh/projects/routing-pipeline/scripts && ./start_streamlit.sh
```

---

**Service URLs:**
- **Streamlit App:** http://localhost:8501
- **API Gateway:** http://localhost:8000 (docs at /docs)
- **Routing Server:** C++ backend (internal)
