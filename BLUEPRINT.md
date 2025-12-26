# Dyson-MCP Project Blueprint

## Project Status Tracker

Track implementation progress across all phases. Check boxes as features are completed.

---

## Phase 0: Foundation
**Status**: In Progress
**Goal**: Repository structure and development environment

- [x] Repository structure creation
- [x] README.md with project vision
- [x] pyproject.toml configuration
- [x] .gitignore setup
- [ ] Development environment documentation
- [ ] C# project file (.csproj) for BepInEx plugin
- [ ] Python package structure (__init__.py files)
- [ ] Initial commit and push

---

## Phase 1A: Save File Analysis (Offline Mode)
**Status**: Not Started
**Goal**: Parse DSP save files and provide basic factory analysis

- [ ] Integration with qhgz2013/dsp_save_parser
- [ ] FactoryState data model (`src/mcp_server/models/factory_state.py`)
- [ ] SaveFileParser data source (`src/mcp_server/data_sources/save_parser.py`)
- [ ] `load_save_analysis` MCP tool
- [ ] `get_factory_snapshot` MCP tool
- [ ] Basic bottleneck detection algorithm
- [ ] Unit tests with real save file fixtures
- [ ] Test save file acquisition

**Success Criteria**:
- Parse .dsv files in <5 seconds for typical saves
- Extract production rates, power, and inventory data
- Handle corrupted saves gracefully

---

## Phase 1B: BepInEx Plugin
**Status**: Not Started
**Goal**: Real-time game data extraction via Harmony patches

- [ ] BepInEx plugin initialization (Plugin.cs)
- [ ] Harmony patch infrastructure
- [ ] ProductionPatch - track assembler output
- [ ] PowerPatch - track power generation/consumption
- [ ] LogisticsPatch - track belt throughput
- [ ] MetricsCollector for aggregating data
- [ ] MetricsSnapshot data model
- [ ] WebSocket server implementation
- [ ] Configuration system (BepInEx config)
- [ ] Plugin testing in-game

**Success Criteria**:
- Plugin loads without crashing DSP
- <5% FPS impact during metric collection
- WebSocket streams JSON metrics at 1Hz

---

## Phase 2: Real-Time Integration
**Status**: Not Started
**Goal**: Connect MCP server to live game data

- [ ] WebSocket client in MCP server
- [ ] RealTimeStream data source
- [ ] Data source router (real-time → save fallback)
- [ ] Tool migration to real-time mode
- [ ] Latency optimization (<200ms)
- [ ] Connection resilience (reconnect logic)
- [ ] Integration testing with running game

**Success Criteria**:
- <200ms latency from game state to MCP response
- Graceful fallback to save file when game not running
- Stable WebSocket connection for extended play sessions

---

## Phase 3: Optimization Engine
**Status**: Not Started
**Goal**: Advanced analysis algorithms

- [ ] Recipe database construction (all DSP recipes)
- [ ] Item ID mapping file
- [ ] Dependency graph builder
- [ ] Root cause bottleneck analysis
- [ ] BottleneckAnalyzer tool implementation
- [ ] PowerAnalyzer tool implementation
- [ ] LogisticsAnalyzer tool implementation
- [ ] Blueprint format research
- [ ] Blueprint generation engine
- [ ] `generate_optimized_blueprint` tool (P2)

**Success Criteria**:
- >95% accuracy in bottleneck identification
- Analysis completes in <2 seconds
- Blueprints importable into DSP

---

## Phase 4: CI/CD & Polish
**Status**: Not Started
**Goal**: Production-ready release

- [ ] GitHub Actions: Build BepInEx plugin
- [ ] GitHub Actions: Run Python tests
- [ ] GitHub Actions: Release automation
- [ ] >80% Python test coverage
- [ ] >60% C# test coverage
- [ ] Comprehensive documentation
- [ ] Installation guide
- [ ] Demo video: Bottleneck detection
- [ ] Demo video: Power analysis
- [ ] Portfolio integration

**Success Criteria**:
- CI/CD pipeline operational
- All tests passing
- Documentation complete

---

## Quick Reference

### Key Files

| Component | Primary File |
|-----------|-------------|
| MCP Server Entry | `src/mcp_server/server.py` |
| Plugin Entry | `src/bepinex_plugin/Plugin.cs` |
| Factory State Model | `src/mcp_server/models/factory_state.py` |
| Save Parser | `src/mcp_server/data_sources/save_parser.py` |
| Real-Time Stream | `src/mcp_server/data_sources/realtime_stream.py` |
| Item IDs | `src/shared/item_ids.json` |
| Recipe Database | `src/mcp_server/utils/recipe_database.py` |

### MCP Tools

| Tool | Priority | Status |
|------|----------|--------|
| `get_factory_snapshot` | P0 | Not Started |
| `load_save_analysis` | P0 | Not Started |
| `analyze_production_bottlenecks` | P0 | Not Started |
| `analyze_power_grid` | P1 | Not Started |
| `analyze_logistics_saturation` | P1 | Not Started |
| `generate_optimized_blueprint` | P2 | Not Started |

### Performance Targets

| Metric | Target | Maximum |
|--------|--------|---------|
| Real-time query | <100ms | 200ms |
| Bottleneck analysis | <1s | 2s |
| Save file parsing | <3s | 5s |
| FPS impact | <2% | 5% |

---

## Notes

_Add implementation notes, blockers, and decisions here as work progresses._

---

**Last Updated**: 2024-12-26
**Current Phase**: Phase 0 (Foundation)
