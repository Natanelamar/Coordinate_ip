# OpenShift Deployment Guide: Coordinate IP Services

**Mentor's Note**: This guide walks you through deploying your existing two-service application to OpenShift using Kubernetes YAML files. We'll work step-by-step, understanding *why* each piece exists before creating it. You'll write the YAML files yourself—I'm here to guide you through the thinking process.

---

## 1. High-Level Architecture

### What You Have

Your project consists of three components:

**Service A (Port 8000)** - FastAPI application
- **Role**: Entry point that receives IP addresses
- **Behavior**: Calls external API (ip-api.com) to get coordinates, then forwards results to Service B
- **Type**: Stateless
- **Dependencies**: Needs to communicate with Service B

**Service B (Port 8080)** - FastAPI application  
- **Role**: Data receiver and storage manager
- **Behavior**: Receives coordinate data from Service A and stores it in Redis
- **Type**: Stateless (the app itself)
- **Dependencies**: Requires Redis connection

**Redis (Port 6379)** - In-memory data store
- **Role**: Persistent storage for IP-to-coordinate mappings
- **Behavior**: Stores data in key-value format
- **Type**: Stateful (data must survive pod restarts)
- **Dependencies**: None

### How They Communicate

In your current local setup:
- Service A calls Service B at `http://localhost:8080/receive`
- Service B connects to Redis at `localhost:6379`

In Kubernetes/OpenShift:
- Service A will call Service B using Kubernetes DNS: `http://service-b:8080/receive`
- Service B will connect to Redis using: `redis:6379`
- Each component gets a **Service** resource that provides stable DNS and load balancing
- Kubernetes internal DNS automatically resolves service names to cluster IPs

### Deployment Strategy

- **Service A & B**: Use `Deployment` (stateless, can scale horizontally, pods are replaceable)
- **Redis**: Use `StatefulSet` (stateful, needs persistent storage, stable network identity)

---

## 2. Kubernetes Resource Planning

You'll need to create **7 YAML files** organized in a new `k8s/` directory at your project root.

### File Structure

```
Coordinate_ip/
├── k8s/
│   ├── service-a-deployment.yaml
│   ├── service-a-service.yaml
│   ├── service-b-deployment.yaml
│   ├── service-b-service.yaml
│   ├── redis-statefulset.yaml
│   ├── redis-service.yaml
│   └── redis-pvc.yaml
├── service-a/
├── service-b/
└── requirements.txt
```

### Why This Organization?

- Keeps deployment configs separate from application code
- Easy to version control infrastructure changes
- Clear visibility of what's deployed
- Standard practice in production environments

---

### Resource Breakdown

#### 1. `service-a-deployment.yaml`
**What**: Defines how Service A pods run  
**Why**: Tells Kubernetes how many replicas, which container image, ports, environment variables  
**Key Responsibility**: Ensures Service A is always running and healthy  

**Before writing, think about**:
- What container image will you use? (You'll need to build and push one, or use a base Python image)
- How many replicas do you need? (Start with 1)
- What port does the container expose? (8000)
- Does it need environment variables? (Yes - Service B URL)

---

#### 2. `service-a-service.yaml`
**What**: Network endpoint for Service A  
**Why**: Provides stable DNS name and load balancing across Service A pods  
**Key Responsibility**: Makes Service A discoverable within the cluster  

**Before writing, think about**:
- What port should the Service expose? (8000)
- What port does it forward to on the pod? (8000)
- Do you need external access? (Probably yes - you'll use a Route later)
- What label selector matches your Deployment pods?

---

#### 3. `service-b-deployment.yaml`
**What**: Defines how Service B pods run  
**Why**: Same as Service A, but for the storage service  
**Key Responsibility**: Keeps Service B available to receive data  

**Before writing, think about**:
- Container image (same considerations as Service A)
- Port exposure (8080)
- Environment variables (Redis host and port)
- How it differs from Service A (different port, different env vars)

---

#### 4. `service-b-service.yaml`
**What**: Network endpoint for Service B  
**Why**: Allows Service A to reach Service B using DNS name `service-b`  
**Key Responsibility**: Internal service discovery  

**Before writing, think about**:
- This is **internal only** (no external Route needed)
- Port mapping (8080 → 8080)
- Label selector must match Service B Deployment

---

#### 5. `redis-statefulset.yaml`
**What**: Defines how Redis runs with stable identity  
**Why**: StatefulSet (not Deployment) because Redis needs persistent storage  
**Key Responsibility**: Maintains data across pod restarts  

**Before writing, think about**:
- Why StatefulSet? (Stable network ID, ordered deployment, persistent storage)
- Volume mounting (where Redis stores data: `/data`)
- Which Redis image to use (official `redis:7-alpine` is lightweight)
- Resource limits (Redis can be memory-intensive)

---

#### 6. `redis-service.yaml`
**What**: Network endpoint for Redis  
**Why**: Provides stable DNS name `redis` for Service B to connect  
**Key Responsibility**: Service discovery for database connections  

**Before writing, think about**:
- Headless vs ClusterIP? (ClusterIP is fine for single Redis instance)
- Port 6379 (Redis default)
- Internal only (no external access needed)

---

#### 7. `redis-pvc.yaml`
**What**: PersistentVolumeClaim for Redis data  
**Why**: Requests storage from OpenShift to persist data beyond pod lifecycle  
**Key Responsibility**: Data durability  

**Before writing, think about**:
- How much storage? (Start with 1Gi for testing)
- Access mode: ReadWriteOnce (single pod writes)
- Storage class (OpenShift provides defaults)

---

## 3. Step-by-Step YAML Writing Guidance

### General YAML Structure Principles

Every Kubernetes resource has this structure:

```yaml
apiVersion: <api-version>
kind: <resource-type>
metadata:
  name: <unique-name>
  labels:
    <key>: <value>
spec:
  <resource-specific-configuration>
```

**Critical Rule**: Labels in `metadata` and selectors in `spec` must match exactly.

---

### Writing Deployments (Service A & B)

**Minimal Required Fields**:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: service-a
  labels:
    app: service-a
spec:
  replicas: 1
  selector:
    matchLabels:
      app: service-a  # MUST match template labels
  template:
    metadata:
      labels:
        app: service-a  # MUST match selector
    spec:
      containers:
      - name: service-a
        image: <your-image>
        ports:
        - containerPort: 8000
        env:
        - name: SERVICE_B_URL
          value: "http://service-b:8080"
```

**Common Mistakes**:
- Label mismatch between `selector.matchLabels` and `template.metadata.labels`
- Wrong `containerPort` (must match what your app listens on)
- Forgetting environment variables (your code has hardcoded localhost URLs)

**What Values Must Match**:
- `spec.selector.matchLabels.app` = `spec.template.metadata.labels.app`
- `containerPort` = port in your `main.py` (8000 for A, 8080 for B)

**What NOT to Add Yet**:
- Resource limits (add after testing)
- Liveness/readiness probes (add after basic deployment works)
- Multiple replicas (start with 1)
- Image pull secrets (unless using private registry)

**Critical Note**: You'll need to modify your application code to use environment variables instead of hardcoded `localhost` URLs. Specifically:
- `service-a/app/services.py` line 21: Change `http://localhost:8080` to read from env var
- `service-b/app/storage.py` line 5: Change `localhost` to read from env var

---

### Writing Services

**Minimal Required Fields**:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: service-a
spec:
  selector:
    app: service-a  # MUST match Deployment labels
  ports:
  - port: 8000        # Port the Service exposes
    targetPort: 8000  # Port on the Pod
  type: ClusterIP
```

**Common Mistakes**:
- `selector` doesn't match Deployment labels → Service won't route traffic
- `port` vs `targetPort` confusion:
  - `port`: What other services use to call this service
  - `targetPort`: What port your container listens on
- Using `NodePort` or `LoadBalancer` when `ClusterIP` is sufficient

**What Values Must Match**:
- `spec.selector.app` must match your Deployment's pod labels
- `spec.ports.targetPort` must match Deployment's `containerPort`

**What NOT to Add Yet**:
- Multiple ports (unless your app actually uses them)
- Session affinity (not needed for stateless APIs)

---

### Writing StatefulSet (Redis)

**Minimal Required Fields**:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
spec:
  serviceName: redis  # Required for StatefulSet
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-data
          mountPath: /data
  volumeClaimTemplates:
  - metadata:
      name: redis-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 1Gi
```

**Why StatefulSet vs Deployment**:
- Stable pod names (redis-0, not random hash)
- Ordered deployment and scaling
- Automatic PVC creation per replica
- Stable storage that follows the pod

**Common Mistakes**:
- Forgetting `serviceName` field (required for StatefulSet)
- Wrong `volumeMounts.mountPath` (Redis stores data in `/data`)
- Not understanding `volumeClaimTemplates` creates PVCs automatically

**What NOT to Add Yet**:
- Redis clustering (single instance is fine)
- Redis password (add security after basic deployment works)
- Custom Redis configuration

---

### Writing PersistentVolumeClaim

**Note**: If using StatefulSet with `volumeClaimTemplates`, you don't need a separate PVC file. The StatefulSet creates it automatically. However, if you prefer explicit control:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-data
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

**Access Modes**:
- `ReadWriteOnce`: One pod can mount as read-write (correct for Redis)
- `ReadOnlyMany`: Multiple pods read-only (not for Redis)
- `ReadWriteMany`: Multiple pods read-write (expensive, not needed)

---

## 4. Local Validation Workflow

### Before Applying to OpenShift

**1. YAML Syntax Validation**

```bash
# Check if YAML is valid
kubectl apply --dry-run=client -f k8s/service-a-deployment.yaml
```

This validates syntax and required fields without actually creating resources.

**2. Label Consistency Check**

Manually verify these match:
- Deployment `selector.matchLabels` = Deployment `template.metadata.labels`
- Service `selector` = Deployment `template.metadata.labels`

**3. Port Consistency Check**

Create a mental map:
- Service A: Container listens on 8000 → Deployment `containerPort: 8000` → Service `targetPort: 8000`
- Service B: Container listens on 8080 → Deployment `containerPort: 8080` → Service `targetPort: 8080`
- Redis: Container listens on 6379 → StatefulSet `containerPort: 6379` → Service `targetPort: 6379`

**4. Environment Variable Check**

Ensure your Deployments set:
- Service A needs: `SERVICE_B_URL=http://service-b:8080`
- Service B needs: `REDIS_HOST=redis` and `REDIS_PORT=6379`

**5. Think Like Kubernetes**

Ask yourself:
- Can Service A find Service B? (Yes, via DNS name `service-b`)
- Can Service B find Redis? (Yes, via DNS name `redis`)
- Will data survive pod restarts? (Yes, Redis uses PVC)
- What happens if a pod crashes? (Deployment recreates it automatically)

---

## 5. Deployment Flow (Terminal Only)

### Prerequisites

You need:
- OpenShift CLI (`oc`) installed
- Access to an OpenShift cluster
- Container images for Service A and B (pushed to a registry)

**Note on Container Images**: Your YAML files will reference container images. You'll need to either:
1. Build images and push to a registry (Docker Hub, Quay.io, OpenShift internal registry)
2. Use OpenShift's Source-to-Image (S2I) to build from source

For now, assume you have images ready. We'll use placeholders like `your-registry/service-a:latest`.

---

### Step 1: Login to OpenShift

```bash
oc login <your-openshift-cluster-url>
```

**What this does**: Authenticates you and sets up kubectl/oc context.

You'll be prompted for credentials. After successful login, you'll see your current project.

---

### Step 2: Create or Select a Project

```bash
# Create a new project (namespace)
oc new-project coordinate-ip-app

# OR switch to existing project
oc project coordinate-ip-app
```

**What this does**: 
- Creates an isolated namespace for your resources
- All subsequent commands operate in this namespace
- Provides resource quotas and access control boundaries

**Verify**:
```bash
oc project
# Should show: Using project "coordinate-ip-app"
```

---

### Step 3: Apply YAML Files (Correct Order Matters)

**Order of Operations**:

1. **Storage first** (Redis needs it)
2. **StatefulSets/Deployments** (apps need to start)
3. **Services** (networking layer)

```bash
# 1. Create Redis storage and StatefulSet
oc apply -f k8s/redis-statefulset.yaml

# 2. Create Redis Service
oc apply -f k8s/redis-service.yaml

# 3. Create Service B (depends on Redis)
oc apply -f k8s/service-b-deployment.yaml
oc apply -f k8s/service-b-service.yaml

# 4. Create Service A (depends on Service B)
oc apply -f k8s/service-a-deployment.yaml
oc apply -f k8s/service-a-service.yaml
```

**Why this order?**
- Redis must be ready before Service B starts (Service B connects to Redis on startup)
- Service B should be ready before Service A starts (though Service A can retry)
- Services can be created anytime, but creating them before Deployments is cleaner

**Alternative (apply all at once)**:
```bash
oc apply -f k8s/
```
Kubernetes will handle dependencies, but you lose visibility into the process.

---

### Step 4: Verify Each Component

#### Check Pods

```bash
oc get pods
```

**What you should see**:
```
NAME                         READY   STATUS    RESTARTS   AGE
redis-0                      1/1     Running   0          2m
service-a-xxxxxxxxxx-xxxxx   1/1     Running   0          1m
service-b-xxxxxxxxxx-xxxxx   1/1     Running   0          1m
```

**What each column means**:
- `READY`: `1/1` means 1 container ready out of 1 total
- `STATUS`: Should be `Running` (if `Pending`, `CrashLoopBackOff`, or `Error`, see debugging section)
- `RESTARTS`: Should be 0 (if increasing, pod is crashing)

**Detailed pod info**:
```bash
oc describe pod <pod-name>
```

This shows events, container status, volume mounts, and error messages.

---

#### Check Services

```bash
oc get services
```

**What you should see**:
```
NAME        TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE
redis       ClusterIP   172.30.xxx.xxx   <none>        6379/TCP   2m
service-a   ClusterIP   172.30.xxx.xxx   <none>        8000/TCP   1m
service-b   ClusterIP   172.30.xxx.xxx   <none>        8080/TCP   1m
```

**Verify**:
- Each service has a `CLUSTER-IP` (internal IP)
- Ports match your configuration
- `TYPE` is `ClusterIP` for internal services

---

#### Check Logs

```bash
# Service A logs
oc logs deployment/service-a

# Service B logs
oc logs deployment/service-b

# Redis logs
oc logs statefulset/redis

# Follow logs in real-time
oc logs -f deployment/service-a
```

**What to look for**:
- Service A: Should show FastAPI startup, no connection errors to Service B
- Service B: Should show FastAPI startup, successful Redis connection
- Redis: Should show "Ready to accept connections"

**Common log errors**:
- `Connection refused`: Target service isn't ready or wrong hostname
- `Name resolution failed`: DNS issue (wrong service name)
- `ModuleNotFoundError`: Missing dependencies in container image

---

#### Check Environment Variables

```bash
oc exec deployment/service-a -- env | grep SERVICE_B_URL
oc exec deployment/service-b -- env | grep REDIS
```

**What this does**: Verifies environment variables are set correctly inside running containers.

---

### Step 5: Expose Service A Externally (Create Route)

Your Service A needs external access for users to send IP addresses.

```bash
oc expose service/service-a
```

**What this does**: Creates an OpenShift Route (similar to Kubernetes Ingress) with automatic DNS and TLS.

**Get the external URL**:
```bash
oc get route service-a
```

You'll see output like:
```
NAME        HOST/PORT                                    PATH   SERVICES    PORT   TERMINATION
service-a   service-a-coordinate-ip-app.apps.cluster...         service-a   8000   
```

**Test it**:
```bash
curl http://<route-url>/
# Should return: {"message": "server is healthy"}
```

---

### Step 6: Test End-to-End Flow

```bash
# Send an IP address to Service A
curl -X POST http://<service-a-route-url>/ip \
  -H "Content-Type: application/json" \
  -d '{"ip_address": "8.8.8.8"}'

# Check if data was stored in Service B
curl http://<service-a-route-url>/all
```

**What should happen**:
1. Service A receives IP, calls external API, gets coordinates
2. Service A sends coordinates to Service B
3. Service B stores in Redis
4. You can retrieve all stored coordinates

---

## 6. Debugging Mindset

### When Pods Don't Start

**Check pod status**:
```bash
oc get pods
oc describe pod <pod-name>
```

**Common issues**:

| Status | Likely Cause | How to Fix |
|--------|-------------|------------|
| `ImagePullBackOff` | Can't pull container image | Check image name, registry credentials |
| `CrashLoopBackOff` | Container starts then crashes | Check logs: `oc logs <pod>` |
| `Pending` | Can't schedule (no resources) | Check events in `describe`, may need more cluster resources |
| `CreateContainerConfigError` | Bad config (env vars, volumes) | Check `describe` for specific error |

**Systematic approach**:
1. `oc get pods` → Identify which pod is failing
2. `oc describe pod <name>` → Read events at bottom
3. `oc logs <name>` → Check application logs
4. `oc get events --sort-by='.lastTimestamp'` → Cluster-wide events

---

### When Services Don't Connect

**Symptom**: Service A can't reach Service B, or Service B can't reach Redis.

**Debug steps**:

1. **Verify Service exists**:
```bash
oc get service service-b
```

2. **Test DNS resolution from inside a pod**:
```bash
oc exec deployment/service-a -- nslookup service-b
```
Should resolve to a cluster IP.

3. **Test connectivity**:
```bash
oc exec deployment/service-a -- curl http://service-b:8080/
```

4. **Check Service selector matches pod labels**:
```bash
oc get service service-b -o yaml | grep selector
oc get pods -l app=service-b
```

If no pods match, the selector is wrong.

**Common mistakes**:
- Typo in service name (service-b vs serviceb)
- Wrong port in URL
- Service selector doesn't match pod labels
- Pods aren't ready yet (check `READY` column)

---

### When Data Doesn't Persist

**Symptom**: Redis data disappears after pod restart.

**Check PVC**:
```bash
oc get pvc
```

Should show:
```
NAME                  STATUS   VOLUME                                     CAPACITY
redis-data-redis-0    Bound    pvc-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx   1Gi
```

**If STATUS is `Pending`**:
- No storage class available
- Insufficient storage quota
- Check: `oc describe pvc redis-data-redis-0`

**Verify volume is mounted**:
```bash
oc describe pod redis-0 | grep -A 5 Mounts
```

Should show `/data` mounted from `redis-data`.

---

### Reading Errors Calmly

**When you see an error**:

1. **Don't panic** → Errors are normal, expected, and informative
2. **Read the full message** → Don't skim, read every word
3. **Identify the resource** → Which pod/service/deployment is affected?
4. **Check the timestamp** → Is this a new error or old?
5. **Google if needed** → Kubernetes errors are well-documented
6. **Change one thing** → Don't change multiple things at once

**Example error workflow**:

```
Error: Back-off pulling image "service-a:latest"
```

**Thought process**:
- "Back-off pulling image" → Image pull problem
- "service-a:latest" → Which image?
- Check: Does this image exist in my registry?
- Check: Does OpenShift have credentials to pull it?
- Fix: Update image name or add image pull secret

---

## 7. Final Notes

### What You Should Understand After Finishing

**Conceptually**:
- How Kubernetes Deployments manage stateless applications
- How StatefulSets differ from Deployments (stable identity, persistent storage)
- How Services provide stable networking and DNS
- How labels and selectors connect resources
- How environment variables replace hardcoded configuration
- The difference between container ports, service ports, and target ports

**Practically**:
- How to write basic Deployment, Service, and StatefulSet YAML
- How to apply resources in the correct order
- How to verify deployments using `get`, `describe`, `logs`
- How to debug common issues systematically
- How to expose services externally with Routes

---

### What You Should Be Able to Explain

To a colleague or in an interview:

1. **"Why did we use a StatefulSet for Redis?"**
   - Because Redis needs persistent storage that survives pod restarts
   - StatefulSets provide stable pod names and persistent volume claims
   - Deployments treat pods as disposable; StatefulSets treat them as stateful

2. **"How does Service A find Service B?"**
   - Kubernetes DNS automatically creates records for Services
   - Service B's Service resource has name `service-b`
   - Any pod can reach it at `http://service-b:8080`
   - The Service routes traffic to pods matching its selector

3. **"What happens if the Service A pod crashes?"**
   - The Deployment controller detects the pod is down
   - It automatically creates a new pod to maintain desired replica count
   - The new pod gets a different name but same labels
   - The Service continues routing traffic to healthy pods

4. **"Why do labels matter so much?"**
   - Services use label selectors to find pods
   - If labels don't match, traffic won't route
   - Labels are how Kubernetes groups and identifies resources
   - They're the glue between Deployments and Services

---

### What NOT to Optimize Yet

**Resist the urge to add**:

- **Horizontal Pod Autoscaling (HPA)**: Get basic deployment working first
- **Resource limits and requests**: Add after observing actual usage
- **Liveness and readiness probes**: Add after confirming app works
- **Multiple replicas**: Start with 1, scale after testing
- **Secrets for sensitive data**: Hardcode for learning, secure later
- **Network policies**: Add security after basic networking works
- **Ingress controllers**: OpenShift Routes are simpler to start
- **Monitoring and logging**: Focus on deployment first
- **CI/CD pipelines**: Manual deployment teaches fundamentals

**Why?**
- Each addition adds complexity and potential failure points
- You need a working baseline before optimizing
- Premature optimization makes debugging harder
- Learn to walk before you run

---

### Next Steps After Successful Deployment

Once everything works:

1. **Add health checks**: Liveness and readiness probes
2. **Set resource limits**: Prevent pods from consuming too much CPU/memory
3. **Externalize configuration**: Use ConfigMaps for non-sensitive config
4. **Secure secrets**: Move hardcoded values to Secrets
5. **Scale horizontally**: Increase replicas, test load balancing
6. **Add monitoring**: Prometheus metrics, logging aggregation
7. **Implement CI/CD**: Automate builds and deployments

But for now, focus on getting the basics right.

---

### A Final Word

Deployment is iterative. Your first attempt won't be perfect, and that's expected. You'll make mistakes with labels, ports, and service names. You'll see pods crash and services fail to connect. This is how everyone learns Kubernetes.

The difference between a junior and senior engineer isn't avoiding errors—it's debugging them systematically and learning from each one.

Take your time. Read error messages carefully. Change one thing at a time. And remember: if it works locally but not in Kubernetes, it's almost always networking, labels, or environment variables.

You've got this.

---

**Author's Note**: This guide is based on your actual project structure with Service A (port 8000), Service B (port 8080), and Redis. Before deploying, you'll need to:

1. **Modify your code** to use environment variables instead of `localhost`
2. **Build container images** for Service A and B
3. **Push images** to a container registry accessible by OpenShift
4. **Create the YAML files** following the guidance above

Good luck with your deployment. Take it step by step, and you'll have a working system on OpenShift soon.
