# Agent Development Learnings

## CoreML On-Device Processing Requirements

### Disk Space Requirements

**Critical Finding**: CoreML models need significant free disk space for Neural Engine (ANE) compilation, not just for storage.

#### Space Breakdown:
- **Model Storage**: ~8GB (Qwen3-Embedding-4B-FP16-Final.mlpackage)
- **Compilation Artifacts**: 15-30GB (temporary files during ANE optimization)
- **Runtime Temp Space**: 5-10GB (during first load and optimization)
- **Safe Minimum**: **50GB free disk space**

#### What Happens with Insufficient Space:
1. CoreML model loads successfully (`ct.models.MLModel` succeeds)
2. Model shows as "ANE/GPU capable" in logs
3. During first inference, ANE compilation starts
4. **Silent Failure**: "LLVM ERROR: IO failure on output stream: No space left on device"
5. **Fallback**: CoreML automatically falls back to CPU
6. **Performance Impact**: 50-100ms → 2000-3000ms (20-50x slower!)

#### Detection:
```python
# Logs will show:
"🤖 Model: Qwen3-4B on cpu"  # ← BAD: Using CPU
"🤖 Model: Qwen3-4B on ane"  # ← GOOD: Using Neural Engine
```

### Memory (RAM) Requirements

- **Minimum**: 8GB total system RAM
- **Recommended**: 16GB+ for CoreML
- **Model Runtime**: 4-6GB per loaded model
- **Peak Usage**: 8-10GB during first load and compilation

### Performance Characteristics

#### With ANE (Optimal):
- **Embedding Generation**: 50-100ms
- **ChromaDB Search**: 20-30ms
- **Total Latency**: 70-130ms

#### With CPU Fallback (Degraded):
- **Embedding Generation**: 2000-3000ms (20-50x slower!)
- **ChromaDB Search**: 20-30ms (same)
- **Total Latency**: 2020-3030ms

### Decision Logic for On-Device vs API

```python
import shutil
import psutil

def should_use_ondevice_processing():
    """
    Determines if system has enough resources for CoreML on-device processing.

    Returns:
        tuple: (should_use_ondevice: bool, reason: str)
    """
    # Check disk space
    disk_usage = shutil.disk_usage("/")
    free_gb = disk_usage.free / (1024**3)

    if free_gb < 30:
        return False, f"Insufficient disk space: {free_gb:.1f}GB free (need 30GB+)"

    # Check available RAM
    mem = psutil.virtual_memory()
    available_gb = mem.available / (1024**3)

    if available_gb < 6:
        return False, f"Insufficient RAM: {available_gb:.1f}GB available (need 6GB+)"

    # Check memory pressure
    if mem.percent > 85:
        return False, f"High memory pressure: {mem.percent}% used"

    return True, f"OK: {free_gb:.1f}GB disk, {available_gb:.1f}GB RAM"

# Usage in voice_server.py:
can_use_ondevice, reason = should_use_ondevice_processing()
if can_use_ondevice:
    os.environ["PAPR_ONDEVICE_PROCESSING"] = "true"
    print(f"✅ Using on-device CoreML: {reason}")
else:
    os.environ["PAPR_ONDEVICE_PROCESSING"] = "false"
    print(f"⚠️  Using API backend: {reason}")
```

## ChromaDB Storage

### Collection Size
- **Tier0**: Typically 150-200 items after filtering
- **Storage**: ~35MB SQLite + binary vector files
- **Memory Usage**: Minimal (memory-mapped files)

### Content Filtering
- **Before**: 200 items from server (some with None content)
- **After**: 176 items (filtered 24 empty items)
- **Impact**: Better search quality, smaller database

## Score Types

### Two Separate Scores:
1. **Query Similarity** (ChromaDB):
   - Cosine similarity between query embedding and memory embedding
   - Computed locally during search
   - Range: -1.0 to 1.0 (typically -0.5 to -0.9 for relevant results)

2. **Relevance Score** (Server):
   - Composite: 60% vector + 30% transition + 20% hotness
   - Computed by tier0_builder.py on memory server
   - Stored in metadata during sync_tiers
   - Range: 0.0 to 1.0

### Display:
- Show both scores separately in UI
- "Query Match" = query_similarity
- "Goal Relevance" = relevance_score (from server)

## Common Issues

### Issue: Slow CoreML Performance
**Symptom**: 2-3 second embedding generation instead of 50-100ms
**Root Cause**: CoreML falling back to CPU due to disk space
**Detection**: Logs show "Model: Qwen3-4B on cpu"
**Fix**: Free up disk space (need 30GB+ free)

### Issue: High Memory Pressure
**Symptom**: macOS shows memory pressure warnings
**Root Cause**: CoreML models + ChromaDB + other apps
**Fix**: Close other apps or use API backend

### Issue: Empty Relevance Scores
**Symptom**: All memories show relevance_score: 0.0
**Root Cause**: Production server doesn't have tier0_builder.py fix
**Fix**: Deploy updated tier0_builder.py that preserves similarity_score

## Database Backend Comparison

### ChromaDB:
- **Storage**: SQLite (metadata) + custom binary (vectors)
- **Good for**: Local/on-device, small-medium datasets (<1M vectors)
- **Performance**: O(n) scan but fast for tier0 (176 items)

### Qdrant:
- **Storage**: RocksDB (metadata) + HNSW index (vectors)
- **Good for**: Server-side, large datasets (1M-100M+ vectors)
- **Performance**: O(log n) approximate nearest neighbor

### Neo4j:
- **Storage**: Custom graph storage engine
- **Good for**: Knowledge graph, relationship queries
- **Performance**: O(1) traversals via pointer-chasing
