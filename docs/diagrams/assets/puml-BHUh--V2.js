function n(o){switch(o){case"index":return`@startuml
title "System Context"
top to bottom direction

hide stereotype
skinparam ranksep 60
skinparam nodesep 30
skinparam {
  arrowFontSize 10
  defaultTextAlignment center
  wrapWidth 200
  maxMessageSize 100
  shadowing false
}

skinparam person<<Developer>>{
  BackgroundColor #A35829
  FontColor #FFE0C2
  BorderColor #7E451D
}
skinparam person<<ExternalClient>>{
  BackgroundColor #A35829
  FontColor #FFE0C2
  BorderColor #7E451D
}
skinparam rectangle<<H3RoutingPlatform>>{
  BackgroundColor #0284c7
  FontColor #f0f9ff
  BorderColor #0369a1
}
person "==Developer\\n\\nUses Streamlit UI for testing and Python SDK for integration" <<Developer>> as Developer
person "==External Client\\n\\nAny application consuming the routing REST API" <<ExternalClient>> as ExternalClient
rectangle "==H3 Routing Platform\\n\\nHigh-performance H3-indexed Contraction Hierarchy routing engine" <<H3RoutingPlatform>> as H3RoutingPlatform

Developer .[#8D8D8D,thickness=2].> H3RoutingPlatform : "<color:#8D8D8D>[...]<color:#8D8D8D>"
ExternalClient .[#8D8D8D,thickness=2].> H3RoutingPlatform : "<color:#8D8D8D>REST API calls<color:#8D8D8D>"
@enduml
`;case"containerView":return`@startuml
title "Container Overview"
top to bottom direction

hide stereotype
skinparam ranksep 60
skinparam nodesep 30
skinparam {
  arrowFontSize 10
  defaultTextAlignment center
  wrapWidth 200
  maxMessageSize 100
  shadowing false
}

skinparam person<<Developer>>{
  BackgroundColor #A35829
  FontColor #FFE0C2
  BorderColor #7E451D
}
skinparam person<<ExternalClient>>{
  BackgroundColor #A35829
  FontColor #FFE0C2
  BorderColor #7E451D
}
skinparam rectangle<<H3RoutingPlatformStreamlitUI>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam rectangle<<H3RoutingPlatformPythonSDK>>{
  BackgroundColor #0284c7
  FontColor #f0f9ff
  BorderColor #0369a1
}
skinparam database<<H3RoutingPlatformOsmData>>{
  BackgroundColor #64748b
  FontColor #f8fafc
  BorderColor #475569
}
skinparam rectangle<<H3RoutingPlatformH3Toolkit>>{
  BackgroundColor #428a4f
  FontColor #f8fafc
  BorderColor #2d5d39
}
skinparam rectangle<<H3RoutingPlatformApiGateway>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam rectangle<<H3RoutingPlatformDuckOSM>>{
  BackgroundColor #428a4f
  FontColor #f8fafc
  BorderColor #2d5d39
}
skinparam rectangle<<H3RoutingPlatformShortcutGenerator>>{
  BackgroundColor #428a4f
  FontColor #f8fafc
  BorderColor #2d5d39
}
skinparam database<<H3RoutingPlatformDuckdb>>{
  BackgroundColor #64748b
  FontColor #f8fafc
  BorderColor #475569
}
skinparam rectangle<<H3RoutingPlatformCppEngine>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
person "==Developer\\n\\nUses Streamlit UI for testing and Python SDK for integration" <<Developer>> as Developer
person "==External Client\\n\\nAny application consuming the routing REST API" <<ExternalClient>> as ExternalClient
rectangle "H3 Routing Platform" <<H3RoutingPlatform>> as H3RoutingPlatform {
  skinparam RectangleBorderColor<<H3RoutingPlatform>> #0284c7
  skinparam RectangleFontColor<<H3RoutingPlatform>> #0284c7
  skinparam RectangleBorderStyle<<H3RoutingPlatform>> dashed

  rectangle "==Streamlit UI\\n<size:10>[Python / Streamlit]</size>\\n\\nInteractive map visualization and debugging interface" <<H3RoutingPlatformStreamlitUI>> as H3RoutingPlatformStreamlitUI
  rectangle "==Python SDK\\n<size:10>[Python]</size>\\n\\nh3-routing-client package for programmatic access" <<H3RoutingPlatformPythonSDK>> as H3RoutingPlatformPythonSDK
  database "==OpenStreetMap PBF\\n\\nRaw map data source" <<H3RoutingPlatformOsmData>> as H3RoutingPlatformOsmData
  rectangle "==H3 Toolkit\\n<size:10>[C++ / Python]</size>\\n\\nShared H3 spatial utilities library" <<H3RoutingPlatformH3Toolkit>> as H3RoutingPlatformH3Toolkit
  rectangle "==API Gateway\\n<size:10>[Python / FastAPI]</size>\\n\\nREST API on port 8000, coordinates dataset loading and request translation" <<H3RoutingPlatformApiGateway>> as H3RoutingPlatformApiGateway
  rectangle "==duckOSM\\n<size:10>[Python / DuckDB]</size>\\n\\nConverts OpenStreetMap PBF files to road network in DuckDB" <<H3RoutingPlatformDuckOSM>> as H3RoutingPlatformDuckOSM
  rectangle "==Shortcut Generator\\n<size:10>[Python / DuckDB]</size>\\n\\n4-phase H3 hierarchy processor for contraction shortcuts" <<H3RoutingPlatformShortcutGenerator>> as H3RoutingPlatformShortcutGenerator
  database "==DuckDB Database\\n\\nStores edges, nodes, shortcuts, and dataset info" <<H3RoutingPlatformDuckdb>> as H3RoutingPlatformDuckdb
  rectangle "==C++ Routing Engine\\n<size:10>[C++ / Crow HTTP]</size>\\n\\nHigh-performance engine on port 8082 with CH algorithms" <<H3RoutingPlatformCppEngine>> as H3RoutingPlatformCppEngine
}

Developer .[#8D8D8D,thickness=2].> H3RoutingPlatformStreamlitUI : "<color:#8D8D8D>Uses for visualization<color:#8D8D8D>"
Developer .[#8D8D8D,thickness=2].> H3RoutingPlatformPythonSDK : "<color:#8D8D8D>Integrates via<color:#8D8D8D>"
ExternalClient .[#8D8D8D,thickness=2].> H3RoutingPlatformApiGateway : "<color:#8D8D8D>REST API calls<color:#8D8D8D>"
H3RoutingPlatformStreamlitUI .[#8D8D8D,thickness=2].> H3RoutingPlatformApiGateway : "<color:#8D8D8D>HTTP requests<color:#8D8D8D>"
H3RoutingPlatformApiGateway .[#8D8D8D,thickness=2].> H3RoutingPlatformCppEngine : "<color:#8D8D8D>Route queries (port 8082)<color:#8D8D8D>"
H3RoutingPlatformPythonSDK .[#8D8D8D,thickness=2].> H3RoutingPlatformApiGateway : "<color:#8D8D8D>HTTP requests<color:#8D8D8D>"
H3RoutingPlatformDuckdb .[#8D8D8D,thickness=2].> H3RoutingPlatformCppEngine : "<color:#8D8D8D>Loads at startup<color:#8D8D8D>"
H3RoutingPlatformDuckOSM .[#8D8D8D,thickness=2].> H3RoutingPlatformDuckdb : "<color:#8D8D8D>Creates road graph<color:#8D8D8D>"
H3RoutingPlatformOsmData .[#8D8D8D,thickness=2].> H3RoutingPlatformDuckOSM : "<color:#8D8D8D>Input<color:#8D8D8D>"
H3RoutingPlatformShortcutGenerator .[#8D8D8D,thickness=2].> H3RoutingPlatformDuckdb : "<color:#8D8D8D>Writes shortcuts<color:#8D8D8D>"
H3RoutingPlatformH3Toolkit .[#8D8D8D,thickness=2].> H3RoutingPlatformShortcutGenerator : "<color:#8D8D8D>H3 utilities<color:#8D8D8D>"
H3RoutingPlatformDuckdb .[#8D8D8D,thickness=2].> H3RoutingPlatformShortcutGenerator : "<color:#8D8D8D>Input edges<color:#8D8D8D>"
@enduml
`;case"dataPipeline":return`@startuml
title "Offline Data Pipeline"
top to bottom direction

hide stereotype
skinparam ranksep 60
skinparam nodesep 30
skinparam {
  arrowFontSize 10
  defaultTextAlignment center
  wrapWidth 200
  maxMessageSize 100
  shadowing false
}

skinparam database<<H3RoutingPlatformOsmData>>{
  BackgroundColor #64748b
  FontColor #f8fafc
  BorderColor #475569
}
skinparam rectangle<<H3RoutingPlatformH3Toolkit>>{
  BackgroundColor #428a4f
  FontColor #f8fafc
  BorderColor #2d5d39
}
skinparam rectangle<<H3RoutingPlatformDuckOSM>>{
  BackgroundColor #428a4f
  FontColor #f8fafc
  BorderColor #2d5d39
}
skinparam rectangle<<H3RoutingPlatformShortcutGeneratorDataLoader>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformShortcutGeneratorPhase1>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformShortcutGeneratorCellAssigner>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformShortcutGeneratorPhase2>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformShortcutGeneratorShortestPathSolver>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformShortcutGeneratorPhase3>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformShortcutGeneratorDeduplicator>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformShortcutGeneratorPhase4>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformShortcutGeneratorFinalizer>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam database<<H3RoutingPlatformDuckdb>>{
  BackgroundColor #64748b
  FontColor #f8fafc
  BorderColor #475569
}
database "==OpenStreetMap PBF\\n\\nRaw map data source" <<H3RoutingPlatformOsmData>> as H3RoutingPlatformOsmData
rectangle "==H3 Toolkit\\n<size:10>[C++ / Python]</size>\\n\\nShared H3 spatial utilities library" <<H3RoutingPlatformH3Toolkit>> as H3RoutingPlatformH3Toolkit
rectangle "==duckOSM\\n<size:10>[Python / DuckDB]</size>\\n\\nConverts OpenStreetMap PBF files to road network in DuckDB" <<H3RoutingPlatformDuckOSM>> as H3RoutingPlatformDuckOSM
rectangle "Shortcut Generator" <<H3RoutingPlatformShortcutGenerator>> as H3RoutingPlatformShortcutGenerator {
  skinparam RectangleBorderColor<<H3RoutingPlatformShortcutGenerator>> #428a4f
  skinparam RectangleFontColor<<H3RoutingPlatformShortcutGenerator>> #428a4f
  skinparam RectangleBorderStyle<<H3RoutingPlatformShortcutGenerator>> dashed

  rectangle "==dataLoader\\n\\nLoads edges and edge_graph from DuckDB into working tables" <<H3RoutingPlatformShortcutGeneratorDataLoader>> as H3RoutingPlatformShortcutGeneratorDataLoader
  rectangle "==Phase 1: Forward Chunked\\n\\nProcesses res 15→7 in parallel chunks per partition cell" <<H3RoutingPlatformShortcutGeneratorPhase1>> as H3RoutingPlatformShortcutGeneratorPhase1
  rectangle "==cellAssigner\\n\\nAssigns shortcuts to H3 cells based on LCA resolution" <<H3RoutingPlatformShortcutGeneratorCellAssigner>> as H3RoutingPlatformShortcutGeneratorCellAssigner
  rectangle "==Phase 2: Forward Consolidation\\n\\nMerges cells upward res 6→0, deduplicating via cost" <<H3RoutingPlatformShortcutGeneratorPhase2>> as H3RoutingPlatformShortcutGeneratorPhase2
  rectangle "==shortestPathSolver\\n\\nComputes optimal shortcuts via SciPy/DuckDB graph algorithms" <<H3RoutingPlatformShortcutGeneratorShortestPathSolver>> as H3RoutingPlatformShortcutGeneratorShortestPathSolver
  rectangle "==Phase 3: Backward Consolidation\\n\\nSplits cells downward res 0→7, re-partitioning shortcuts" <<H3RoutingPlatformShortcutGeneratorPhase3>> as H3RoutingPlatformShortcutGeneratorPhase3
  rectangle "==deduplicator\\n\\nRemoves redundant shortcuts keeping minimum cost" <<H3RoutingPlatformShortcutGeneratorDeduplicator>> as H3RoutingPlatformShortcutGeneratorDeduplicator
  rectangle "==Phase 4: Backward Chunked\\n\\nProcesses res 8→15 in parallel chunks, finalizing all resolutions" <<H3RoutingPlatformShortcutGeneratorPhase4>> as H3RoutingPlatformShortcutGeneratorPhase4
  rectangle "==finalizer\\n\\nExports final shortcuts to Parquet and DuckDB schema" <<H3RoutingPlatformShortcutGeneratorFinalizer>> as H3RoutingPlatformShortcutGeneratorFinalizer
}
database "==DuckDB Database\\n\\nStores edges, nodes, shortcuts, and dataset info" <<H3RoutingPlatformDuckdb>> as H3RoutingPlatformDuckdb

H3RoutingPlatformOsmData .[#8D8D8D,thickness=2].> H3RoutingPlatformDuckOSM : "<color:#8D8D8D>Input<color:#8D8D8D>"
H3RoutingPlatformDuckOSM .[#8D8D8D,thickness=2].> H3RoutingPlatformDuckdb : "<color:#8D8D8D>Creates road graph<color:#8D8D8D>"
H3RoutingPlatformShortcutGeneratorFinalizer .[#8D8D8D,thickness=2].> H3RoutingPlatformDuckdb : "<color:#8D8D8D>Writes shortcuts schema<color:#8D8D8D>"
H3RoutingPlatformShortcutGeneratorDataLoader .[#8D8D8D,thickness=2].> H3RoutingPlatformShortcutGeneratorPhase1 : "<color:#8D8D8D>Loads edges<color:#8D8D8D>"
H3RoutingPlatformShortcutGeneratorPhase1 .[#8D8D8D,thickness=2].> H3RoutingPlatformShortcutGeneratorCellAssigner : "<color:#8D8D8D>Per iteration<color:#8D8D8D>"
H3RoutingPlatformShortcutGeneratorPhase1 .[#8D8D8D,thickness=2].> H3RoutingPlatformShortcutGeneratorPhase2 : "<color:#8D8D8D>Chunked outputs<color:#8D8D8D>"
H3RoutingPlatformShortcutGeneratorCellAssigner .[#8D8D8D,thickness=2].> H3RoutingPlatformShortcutGeneratorShortestPathSolver : "<color:#8D8D8D>Active shortcuts<color:#8D8D8D>"
H3RoutingPlatformShortcutGeneratorShortestPathSolver .[#8D8D8D,thickness=2].> H3RoutingPlatformShortcutGeneratorDeduplicator : "<color:#8D8D8D>Optimal paths<color:#8D8D8D>"
H3RoutingPlatformShortcutGeneratorPhase2 .[#8D8D8D,thickness=2].> H3RoutingPlatformShortcutGeneratorPhase3 : "<color:#8D8D8D>Consolidated to res 0<color:#8D8D8D>"
H3RoutingPlatformShortcutGeneratorPhase3 .[#8D8D8D,thickness=2].> H3RoutingPlatformShortcutGeneratorPhase4 : "<color:#8D8D8D>Re-partitioned<color:#8D8D8D>"
H3RoutingPlatformShortcutGeneratorPhase4 .[#8D8D8D,thickness=2].> H3RoutingPlatformShortcutGeneratorFinalizer : "<color:#8D8D8D>All resolutions done<color:#8D8D8D>"
H3RoutingPlatformH3Toolkit .[#8D8D8D,thickness=2].> H3RoutingPlatformShortcutGenerator : "<color:#8D8D8D>H3 utilities<color:#8D8D8D>"
@enduml
`;case"runtimeFlow":return`@startuml
title "Runtime Request Flow"
top to bottom direction

hide stereotype
skinparam ranksep 60
skinparam nodesep 30
skinparam {
  arrowFontSize 10
  defaultTextAlignment center
  wrapWidth 200
  maxMessageSize 100
  shadowing false
}

skinparam person<<Developer>>{
  BackgroundColor #A35829
  FontColor #FFE0C2
  BorderColor #7E451D
}
skinparam person<<ExternalClient>>{
  BackgroundColor #A35829
  FontColor #FFE0C2
  BorderColor #7E451D
}
skinparam rectangle<<H3RoutingPlatformStreamlitUI>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam rectangle<<H3RoutingPlatformPythonSDK>>{
  BackgroundColor #0284c7
  FontColor #f0f9ff
  BorderColor #0369a1
}
skinparam database<<H3RoutingPlatformDuckdb>>{
  BackgroundColor #64748b
  FontColor #f8fafc
  BorderColor #475569
}
skinparam rectangle<<H3RoutingPlatformApiGateway>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam rectangle<<H3RoutingPlatformCppEngine>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
person "==Developer\\n\\nUses Streamlit UI for testing and Python SDK for integration" <<Developer>> as Developer
person "==External Client\\n\\nAny application consuming the routing REST API" <<ExternalClient>> as ExternalClient
rectangle "H3 Routing Platform" <<H3RoutingPlatform>> as H3RoutingPlatform {
  skinparam RectangleBorderColor<<H3RoutingPlatform>> #0284c7
  skinparam RectangleFontColor<<H3RoutingPlatform>> #0284c7
  skinparam RectangleBorderStyle<<H3RoutingPlatform>> dashed

  rectangle "==Streamlit UI\\n<size:10>[Python / Streamlit]</size>\\n\\nInteractive map visualization and debugging interface" <<H3RoutingPlatformStreamlitUI>> as H3RoutingPlatformStreamlitUI
  rectangle "==Python SDK\\n<size:10>[Python]</size>\\n\\nh3-routing-client package for programmatic access" <<H3RoutingPlatformPythonSDK>> as H3RoutingPlatformPythonSDK
  database "==DuckDB Database\\n\\nStores edges, nodes, shortcuts, and dataset info" <<H3RoutingPlatformDuckdb>> as H3RoutingPlatformDuckdb
  rectangle "==API Gateway\\n<size:10>[Python / FastAPI]</size>\\n\\nREST API on port 8000, coordinates dataset loading and request translation" <<H3RoutingPlatformApiGateway>> as H3RoutingPlatformApiGateway
  rectangle "==C++ Routing Engine\\n<size:10>[C++ / Crow HTTP]</size>\\n\\nHigh-performance engine on port 8082 with CH algorithms" <<H3RoutingPlatformCppEngine>> as H3RoutingPlatformCppEngine
}

Developer .[#8D8D8D,thickness=2].> H3RoutingPlatformStreamlitUI : "<color:#8D8D8D>Uses for visualization<color:#8D8D8D>"
Developer .[#8D8D8D,thickness=2].> H3RoutingPlatformPythonSDK : "<color:#8D8D8D>Integrates via<color:#8D8D8D>"
ExternalClient .[#8D8D8D,thickness=2].> H3RoutingPlatformApiGateway : "<color:#8D8D8D>REST API calls<color:#8D8D8D>"
H3RoutingPlatformStreamlitUI .[#8D8D8D,thickness=2].> H3RoutingPlatformApiGateway : "<color:#8D8D8D>HTTP requests<color:#8D8D8D>"
H3RoutingPlatformPythonSDK .[#8D8D8D,thickness=2].> H3RoutingPlatformApiGateway : "<color:#8D8D8D>HTTP requests<color:#8D8D8D>"
H3RoutingPlatformApiGateway .[#8D8D8D,thickness=2].> H3RoutingPlatformCppEngine : "<color:#8D8D8D>Route queries (port 8082)<color:#8D8D8D>"
H3RoutingPlatformDuckdb .[#8D8D8D,thickness=2].> H3RoutingPlatformCppEngine : "<color:#8D8D8D>Loads at startup<color:#8D8D8D>"
@enduml
`;case"engineComponents":return`@startuml
title "C++ Engine Internals"
top to bottom direction

hide stereotype
skinparam ranksep 60
skinparam nodesep 30
skinparam {
  arrowFontSize 10
  defaultTextAlignment center
  wrapWidth 200
  maxMessageSize 100
  shadowing false
}

skinparam rectangle<<H3RoutingPlatformCppEngineQueryAlgorithms>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformCppEngineSpatialIndex>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformCppEngineCsrGraph>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformCppEnginePathExpander>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformCppEngineShortcutGraph>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
rectangle "C++ Routing Engine" <<H3RoutingPlatformCppEngine>> as H3RoutingPlatformCppEngine {
  skinparam RectangleBorderColor<<H3RoutingPlatformCppEngine>> #3b82f6
  skinparam RectangleFontColor<<H3RoutingPlatformCppEngine>> #3b82f6
  skinparam RectangleBorderStyle<<H3RoutingPlatformCppEngine>> dashed

  rectangle "==queryAlgorithms\\n\\nDijkstra, Bidirectional, Pruned, Unidirectional CH" <<H3RoutingPlatformCppEngineQueryAlgorithms>> as H3RoutingPlatformCppEngineQueryAlgorithms
  rectangle "==spatialIndex\\n\\nH3 or R-tree index for nearest edge lookup" <<H3RoutingPlatformCppEngineSpatialIndex>> as H3RoutingPlatformCppEngineSpatialIndex
  rectangle "==csrGraph\\n\\nCompressed Sparse Row graph for memory efficiency" <<H3RoutingPlatformCppEngineCsrGraph>> as H3RoutingPlatformCppEngineCsrGraph
  rectangle "==pathExpander\\n\\nResolves shortcut paths to base edge sequences" <<H3RoutingPlatformCppEnginePathExpander>> as H3RoutingPlatformCppEnginePathExpander
  rectangle "==shortcutGraph\\n\\nGraph with adjacency lists, shortcuts, and edge metadata" <<H3RoutingPlatformCppEngineShortcutGraph>> as H3RoutingPlatformCppEngineShortcutGraph
}

H3RoutingPlatformCppEngineQueryAlgorithms .[#8D8D8D,thickness=2].> H3RoutingPlatformCppEngineShortcutGraph : "<color:#8D8D8D>Queries<color:#8D8D8D>"
H3RoutingPlatformCppEngineSpatialIndex .[#8D8D8D,thickness=2].> H3RoutingPlatformCppEngineShortcutGraph : "<color:#8D8D8D>Indexes edges<color:#8D8D8D>"
H3RoutingPlatformCppEngineQueryAlgorithms .[#8D8D8D,thickness=2].> H3RoutingPlatformCppEngineCsrGraph : "<color:#8D8D8D>Queries<color:#8D8D8D>"
H3RoutingPlatformCppEngineQueryAlgorithms .[#8D8D8D,thickness=2].> H3RoutingPlatformCppEnginePathExpander : "<color:#8D8D8D>Expands shortcuts<color:#8D8D8D>"
@enduml
`;case"apiGatewayComponents":return`@startuml
title "API Gateway Internals"
top to bottom direction

hide stereotype
skinparam ranksep 60
skinparam nodesep 30
skinparam {
  arrowFontSize 10
  defaultTextAlignment center
  wrapWidth 200
  maxMessageSize 100
  shadowing false
}

skinparam rectangle<<H3RoutingPlatformApiGatewayRouteHandler>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformApiGatewayDatasetRegistry>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformApiGatewayCoordTranslator>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
rectangle "API Gateway" <<H3RoutingPlatformApiGateway>> as H3RoutingPlatformApiGateway {
  skinparam RectangleBorderColor<<H3RoutingPlatformApiGateway>> #3b82f6
  skinparam RectangleFontColor<<H3RoutingPlatformApiGateway>> #3b82f6
  skinparam RectangleBorderStyle<<H3RoutingPlatformApiGateway>> dashed

  rectangle "==routeHandler\\n\\nValidates requests and forwards to C++ engine" <<H3RoutingPlatformApiGatewayRouteHandler>> as H3RoutingPlatformApiGatewayRouteHandler
  rectangle "==datasetRegistry\\n\\nManages available datasets from datasets.yaml" <<H3RoutingPlatformApiGatewayDatasetRegistry>> as H3RoutingPlatformApiGatewayDatasetRegistry
  rectangle "==coordTranslator\\n\\nConverts lat/lon to graph edge IDs via spatial index" <<H3RoutingPlatformApiGatewayCoordTranslator>> as H3RoutingPlatformApiGatewayCoordTranslator
}

H3RoutingPlatformApiGatewayRouteHandler .[#8D8D8D,thickness=2].> H3RoutingPlatformApiGatewayDatasetRegistry : "<color:#8D8D8D>Loads from<color:#8D8D8D>"
H3RoutingPlatformApiGatewayRouteHandler .[#8D8D8D,thickness=2].> H3RoutingPlatformApiGatewayCoordTranslator : "<color:#8D8D8D>Uses<color:#8D8D8D>"
@enduml
`;case"shortcutPhases":return`@startuml
title "Shortcut Generator Phases"
top to bottom direction

hide stereotype
skinparam ranksep 60
skinparam nodesep 30
skinparam {
  arrowFontSize 10
  defaultTextAlignment center
  wrapWidth 200
  maxMessageSize 100
  shadowing false
}

skinparam rectangle<<H3RoutingPlatformShortcutGeneratorDataLoader>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformShortcutGeneratorPhase1>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformShortcutGeneratorCellAssigner>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformShortcutGeneratorPhase2>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformShortcutGeneratorShortestPathSolver>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformShortcutGeneratorPhase3>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformShortcutGeneratorDeduplicator>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformShortcutGeneratorPhase4>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformShortcutGeneratorFinalizer>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam database<<H3RoutingPlatformDuckdb>>{
  BackgroundColor #64748b
  FontColor #f8fafc
  BorderColor #475569
}
rectangle "Shortcut Generator" <<H3RoutingPlatformShortcutGenerator>> as H3RoutingPlatformShortcutGenerator {
  skinparam RectangleBorderColor<<H3RoutingPlatformShortcutGenerator>> #428a4f
  skinparam RectangleFontColor<<H3RoutingPlatformShortcutGenerator>> #428a4f
  skinparam RectangleBorderStyle<<H3RoutingPlatformShortcutGenerator>> dashed

  rectangle "==dataLoader\\n\\nLoads edges and edge_graph from DuckDB into working tables" <<H3RoutingPlatformShortcutGeneratorDataLoader>> as H3RoutingPlatformShortcutGeneratorDataLoader
  rectangle "==Phase 1: Forward Chunked\\n\\nProcesses res 15→7 in parallel chunks per partition cell" <<H3RoutingPlatformShortcutGeneratorPhase1>> as H3RoutingPlatformShortcutGeneratorPhase1
  rectangle "==cellAssigner\\n\\nAssigns shortcuts to H3 cells based on LCA resolution" <<H3RoutingPlatformShortcutGeneratorCellAssigner>> as H3RoutingPlatformShortcutGeneratorCellAssigner
  rectangle "==Phase 2: Forward Consolidation\\n\\nMerges cells upward res 6→0, deduplicating via cost" <<H3RoutingPlatformShortcutGeneratorPhase2>> as H3RoutingPlatformShortcutGeneratorPhase2
  rectangle "==shortestPathSolver\\n\\nComputes optimal shortcuts via SciPy/DuckDB graph algorithms" <<H3RoutingPlatformShortcutGeneratorShortestPathSolver>> as H3RoutingPlatformShortcutGeneratorShortestPathSolver
  rectangle "==Phase 3: Backward Consolidation\\n\\nSplits cells downward res 0→7, re-partitioning shortcuts" <<H3RoutingPlatformShortcutGeneratorPhase3>> as H3RoutingPlatformShortcutGeneratorPhase3
  rectangle "==deduplicator\\n\\nRemoves redundant shortcuts keeping minimum cost" <<H3RoutingPlatformShortcutGeneratorDeduplicator>> as H3RoutingPlatformShortcutGeneratorDeduplicator
  rectangle "==Phase 4: Backward Chunked\\n\\nProcesses res 8→15 in parallel chunks, finalizing all resolutions" <<H3RoutingPlatformShortcutGeneratorPhase4>> as H3RoutingPlatformShortcutGeneratorPhase4
  rectangle "==finalizer\\n\\nExports final shortcuts to Parquet and DuckDB schema" <<H3RoutingPlatformShortcutGeneratorFinalizer>> as H3RoutingPlatformShortcutGeneratorFinalizer
}
database "==DuckDB Database\\n\\nStores edges, nodes, shortcuts, and dataset info" <<H3RoutingPlatformDuckdb>> as H3RoutingPlatformDuckdb

H3RoutingPlatformShortcutGeneratorDataLoader .[#8D8D8D,thickness=2].> H3RoutingPlatformShortcutGeneratorPhase1 : "<color:#8D8D8D>Loads edges<color:#8D8D8D>"
H3RoutingPlatformShortcutGeneratorPhase1 .[#8D8D8D,thickness=2].> H3RoutingPlatformShortcutGeneratorCellAssigner : "<color:#8D8D8D>Per iteration<color:#8D8D8D>"
H3RoutingPlatformShortcutGeneratorPhase1 .[#8D8D8D,thickness=2].> H3RoutingPlatformShortcutGeneratorPhase2 : "<color:#8D8D8D>Chunked outputs<color:#8D8D8D>"
H3RoutingPlatformShortcutGeneratorCellAssigner .[#8D8D8D,thickness=2].> H3RoutingPlatformShortcutGeneratorShortestPathSolver : "<color:#8D8D8D>Active shortcuts<color:#8D8D8D>"
H3RoutingPlatformShortcutGeneratorShortestPathSolver .[#8D8D8D,thickness=2].> H3RoutingPlatformShortcutGeneratorDeduplicator : "<color:#8D8D8D>Optimal paths<color:#8D8D8D>"
H3RoutingPlatformShortcutGeneratorPhase2 .[#8D8D8D,thickness=2].> H3RoutingPlatformShortcutGeneratorPhase3 : "<color:#8D8D8D>Consolidated to res 0<color:#8D8D8D>"
H3RoutingPlatformShortcutGeneratorPhase3 .[#8D8D8D,thickness=2].> H3RoutingPlatformShortcutGeneratorPhase4 : "<color:#8D8D8D>Re-partitioned<color:#8D8D8D>"
H3RoutingPlatformShortcutGeneratorPhase4 .[#8D8D8D,thickness=2].> H3RoutingPlatformShortcutGeneratorFinalizer : "<color:#8D8D8D>All resolutions done<color:#8D8D8D>"
H3RoutingPlatformShortcutGeneratorFinalizer .[#8D8D8D,thickness=2].> H3RoutingPlatformDuckdb : "<color:#8D8D8D>Writes shortcuts schema<color:#8D8D8D>"
@enduml
`;case"duckOSMComponents":return`@startuml
title "duckOSM Processing Pipeline"
top to bottom direction

hide stereotype
skinparam ranksep 60
skinparam nodesep 30
skinparam {
  arrowFontSize 10
  defaultTextAlignment center
  wrapWidth 200
  maxMessageSize 100
  shadowing false
}

skinparam rectangle<<H3RoutingPlatformDuckOSMPbfLoader>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformDuckOSMRoadFilter>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformDuckOSMGraphBuilder>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformDuckOSMGraphSimplifier>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformDuckOSMSpeedProcessor>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformDuckOSMCostCalculator>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformDuckOSMRestrictionProcessor>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformDuckOSMEdgeGraphBuilder>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
skinparam rectangle<<H3RoutingPlatformDuckOSMH3Indexer>>{
  BackgroundColor #6366f1
  FontColor #eef2ff
  BorderColor #4f46e5
}
rectangle "duckOSM" <<H3RoutingPlatformDuckOSM>> as H3RoutingPlatformDuckOSM {
  skinparam RectangleBorderColor<<H3RoutingPlatformDuckOSM>> #428a4f
  skinparam RectangleFontColor<<H3RoutingPlatformDuckOSM>> #428a4f
  skinparam RectangleBorderStyle<<H3RoutingPlatformDuckOSM>> dashed

  rectangle "==pbfLoader\\n\\nLoads PBF via ST_READOSM extension" <<H3RoutingPlatformDuckOSMPbfLoader>> as H3RoutingPlatformDuckOSMPbfLoader
  rectangle "==roadFilter\\n\\nFilters ways to highway types only" <<H3RoutingPlatformDuckOSMRoadFilter>> as H3RoutingPlatformDuckOSMRoadFilter
  rectangle "==graphBuilder\\n\\nCreates directed edges from OSM ways" <<H3RoutingPlatformDuckOSMGraphBuilder>> as H3RoutingPlatformDuckOSMGraphBuilder
  rectangle "==graphSimplifier\\n\\nContracts degree-2 nodes to simplify graph" <<H3RoutingPlatformDuckOSMGraphSimplifier>> as H3RoutingPlatformDuckOSMGraphSimplifier
  rectangle "==speedProcessor\\n\\nInfers speed limits from highway tags" <<H3RoutingPlatformDuckOSMSpeedProcessor>> as H3RoutingPlatformDuckOSMSpeedProcessor
  rectangle "==costCalculator\\n\\nCalculates travel time costs per edge" <<H3RoutingPlatformDuckOSMCostCalculator>> as H3RoutingPlatformDuckOSMCostCalculator
  rectangle "==restrictionProcessor\\n\\nExtracts turn restrictions from relations" <<H3RoutingPlatformDuckOSMRestrictionProcessor>> as H3RoutingPlatformDuckOSMRestrictionProcessor
  rectangle "==edgeGraphBuilder\\n\\nBuilds edge-to-edge adjacency graph" <<H3RoutingPlatformDuckOSMEdgeGraphBuilder>> as H3RoutingPlatformDuckOSMEdgeGraphBuilder
  rectangle "==h3Indexer\\n\\nAdds H3 cell indexing to edges" <<H3RoutingPlatformDuckOSMH3Indexer>> as H3RoutingPlatformDuckOSMH3Indexer
}

H3RoutingPlatformDuckOSMPbfLoader .[#8D8D8D,thickness=2].> H3RoutingPlatformDuckOSMRoadFilter : "<color:#8D8D8D>Flows to<color:#8D8D8D>"
H3RoutingPlatformDuckOSMRoadFilter .[#8D8D8D,thickness=2].> H3RoutingPlatformDuckOSMGraphBuilder : "<color:#8D8D8D>Flows to<color:#8D8D8D>"
H3RoutingPlatformDuckOSMGraphBuilder .[#8D8D8D,thickness=2].> H3RoutingPlatformDuckOSMGraphSimplifier : "<color:#8D8D8D>Flows to<color:#8D8D8D>"
H3RoutingPlatformDuckOSMGraphSimplifier .[#8D8D8D,thickness=2].> H3RoutingPlatformDuckOSMSpeedProcessor : "<color:#8D8D8D>Flows to<color:#8D8D8D>"
H3RoutingPlatformDuckOSMSpeedProcessor .[#8D8D8D,thickness=2].> H3RoutingPlatformDuckOSMCostCalculator : "<color:#8D8D8D>Flows to<color:#8D8D8D>"
H3RoutingPlatformDuckOSMCostCalculator .[#8D8D8D,thickness=2].> H3RoutingPlatformDuckOSMRestrictionProcessor : "<color:#8D8D8D>Flows to<color:#8D8D8D>"
H3RoutingPlatformDuckOSMRestrictionProcessor .[#8D8D8D,thickness=2].> H3RoutingPlatformDuckOSMEdgeGraphBuilder : "<color:#8D8D8D>Flows to<color:#8D8D8D>"
H3RoutingPlatformDuckOSMEdgeGraphBuilder .[#8D8D8D,thickness=2].> H3RoutingPlatformDuckOSMH3Indexer : "<color:#8D8D8D>Flows to<color:#8D8D8D>"
@enduml
`;default:throw new Error("Unknown viewId: "+o)}}export{n as pumlSource};
