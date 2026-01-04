function o(t){switch(t){case"index":return`---
title: "System Context"
---
graph TB
  Developer[fa:fa-user Developer]
  ExternalClient[fa:fa-user External Client]
  H3RoutingPlatform[H3 Routing Platform]
  Developer -. "[...]" .-> H3RoutingPlatform
  ExternalClient -. "REST API calls" .-> H3RoutingPlatform
`;case"containerView":return`---
title: "Container Overview"
---
graph TB
  Developer[fa:fa-user Developer]
  ExternalClient[fa:fa-user External Client]
  subgraph H3RoutingPlatform["H3 Routing Platform"]
    H3RoutingPlatform.StreamlitUI[Streamlit UI]
    H3RoutingPlatform.PythonSDK[Python SDK]
    H3RoutingPlatform.OsmData([OpenStreetMap PBF])
    H3RoutingPlatform.H3Toolkit[H3 Toolkit]
    H3RoutingPlatform.ApiGateway[API Gateway]
    H3RoutingPlatform.DuckOSM[duckOSM]
    H3RoutingPlatform.ShortcutGenerator[Shortcut Generator]
    H3RoutingPlatform.Duckdb([DuckDB Database])
    H3RoutingPlatform.CppEngine[C++ Routing Engine]
  end
  Developer -. "Uses for visualization" .-> H3RoutingPlatform.StreamlitUI
  Developer -. "Integrates via" .-> H3RoutingPlatform.PythonSDK
  ExternalClient -. "REST API calls" .-> H3RoutingPlatform.ApiGateway
  H3RoutingPlatform.StreamlitUI -. "HTTP requests" .-> H3RoutingPlatform.ApiGateway
  H3RoutingPlatform.ApiGateway -. "Route queries (port 8082)" .-> H3RoutingPlatform.CppEngine
  H3RoutingPlatform.PythonSDK -. "HTTP requests" .-> H3RoutingPlatform.ApiGateway
  H3RoutingPlatform.Duckdb -. "Loads at startup" .-> H3RoutingPlatform.CppEngine
  H3RoutingPlatform.DuckOSM -. "Creates road graph" .-> H3RoutingPlatform.Duckdb
  H3RoutingPlatform.OsmData -. "Input" .-> H3RoutingPlatform.DuckOSM
  H3RoutingPlatform.ShortcutGenerator -. "Writes shortcuts" .-> H3RoutingPlatform.Duckdb
  H3RoutingPlatform.H3Toolkit -. "H3 utilities" .-> H3RoutingPlatform.ShortcutGenerator
  H3RoutingPlatform.Duckdb -. "Input edges" .-> H3RoutingPlatform.ShortcutGenerator
`;case"dataPipeline":return`---
title: "Offline Data Pipeline"
---
graph TB
  H3RoutingPlatformOsmData([OpenStreetMap PBF])
  H3RoutingPlatformH3Toolkit[H3 Toolkit]
  H3RoutingPlatformDuckOSM[duckOSM]
  subgraph H3RoutingPlatformShortcutGenerator["Shortcut Generator"]
    H3RoutingPlatformShortcutGenerator.DataLoader[dataLoader]
    H3RoutingPlatformShortcutGenerator.Phase1[Phase 1: Forward Chunked]
    H3RoutingPlatformShortcutGenerator.CellAssigner[cellAssigner]
    H3RoutingPlatformShortcutGenerator.Phase2[Phase 2: Forward Consolidation]
    H3RoutingPlatformShortcutGenerator.ShortestPathSolver[shortestPathSolver]
    H3RoutingPlatformShortcutGenerator.Phase3[Phase 3: Backward Consolidation]
    H3RoutingPlatformShortcutGenerator.Deduplicator[deduplicator]
    H3RoutingPlatformShortcutGenerator.Phase4[Phase 4: Backward Chunked]
    H3RoutingPlatformShortcutGenerator.Finalizer[finalizer]
  end
  H3RoutingPlatformDuckdb([DuckDB Database])
  H3RoutingPlatformOsmData -. "Input" .-> H3RoutingPlatformDuckOSM
  H3RoutingPlatformDuckOSM -. "Creates road graph" .-> H3RoutingPlatformDuckdb
  H3RoutingPlatformShortcutGenerator.Finalizer -. "Writes shortcuts schema" .-> H3RoutingPlatformDuckdb
  H3RoutingPlatformShortcutGenerator.DataLoader -. "Loads edges" .-> H3RoutingPlatformShortcutGenerator.Phase1
  H3RoutingPlatformShortcutGenerator.Phase1 -. "Per iteration" .-> H3RoutingPlatformShortcutGenerator.CellAssigner
  H3RoutingPlatformShortcutGenerator.Phase1 -. "Chunked outputs" .-> H3RoutingPlatformShortcutGenerator.Phase2
  H3RoutingPlatformShortcutGenerator.CellAssigner -. "Active shortcuts" .-> H3RoutingPlatformShortcutGenerator.ShortestPathSolver
  H3RoutingPlatformShortcutGenerator.ShortestPathSolver -. "Optimal paths" .-> H3RoutingPlatformShortcutGenerator.Deduplicator
  H3RoutingPlatformShortcutGenerator.Phase2 -. "Consolidated to res 0" .-> H3RoutingPlatformShortcutGenerator.Phase3
  H3RoutingPlatformShortcutGenerator.Phase3 -. "Re-partitioned" .-> H3RoutingPlatformShortcutGenerator.Phase4
  H3RoutingPlatformShortcutGenerator.Phase4 -. "All resolutions done" .-> H3RoutingPlatformShortcutGenerator.Finalizer
  H3RoutingPlatformH3Toolkit -. "H3 utilities" .-> H3RoutingPlatformShortcutGenerator
`;case"runtimeFlow":return`---
title: "Runtime Request Flow"
---
graph TB
  Developer[fa:fa-user Developer]
  ExternalClient[fa:fa-user External Client]
  subgraph H3RoutingPlatform["H3 Routing Platform"]
    H3RoutingPlatform.StreamlitUI[Streamlit UI]
    H3RoutingPlatform.PythonSDK[Python SDK]
    H3RoutingPlatform.Duckdb([DuckDB Database])
    H3RoutingPlatform.ApiGateway[API Gateway]
    H3RoutingPlatform.CppEngine[C++ Routing Engine]
  end
  Developer -. "Uses for visualization" .-> H3RoutingPlatform.StreamlitUI
  Developer -. "Integrates via" .-> H3RoutingPlatform.PythonSDK
  ExternalClient -. "REST API calls" .-> H3RoutingPlatform.ApiGateway
  H3RoutingPlatform.StreamlitUI -. "HTTP requests" .-> H3RoutingPlatform.ApiGateway
  H3RoutingPlatform.PythonSDK -. "HTTP requests" .-> H3RoutingPlatform.ApiGateway
  H3RoutingPlatform.ApiGateway -. "Route queries (port 8082)" .-> H3RoutingPlatform.CppEngine
  H3RoutingPlatform.Duckdb -. "Loads at startup" .-> H3RoutingPlatform.CppEngine
`;case"engineComponents":return`---
title: "C++ Engine Internals"
---
graph TB
  subgraph H3RoutingPlatformCppEngine["C++ Routing Engine"]
    H3RoutingPlatformCppEngine.QueryAlgorithms[queryAlgorithms]
    H3RoutingPlatformCppEngine.SpatialIndex[spatialIndex]
    H3RoutingPlatformCppEngine.CsrGraph[csrGraph]
    H3RoutingPlatformCppEngine.PathExpander[pathExpander]
    H3RoutingPlatformCppEngine.ShortcutGraph[shortcutGraph]
  end
  H3RoutingPlatformCppEngine.QueryAlgorithms -. "Queries" .-> H3RoutingPlatformCppEngine.ShortcutGraph
  H3RoutingPlatformCppEngine.SpatialIndex -. "Indexes edges" .-> H3RoutingPlatformCppEngine.ShortcutGraph
  H3RoutingPlatformCppEngine.QueryAlgorithms -. "Queries" .-> H3RoutingPlatformCppEngine.CsrGraph
  H3RoutingPlatformCppEngine.QueryAlgorithms -. "Expands shortcuts" .-> H3RoutingPlatformCppEngine.PathExpander
`;case"apiGatewayComponents":return`---
title: "API Gateway Internals"
---
graph TB
  subgraph H3RoutingPlatformApiGateway["API Gateway"]
    H3RoutingPlatformApiGateway.RouteHandler[routeHandler]
    H3RoutingPlatformApiGateway.DatasetRegistry[datasetRegistry]
    H3RoutingPlatformApiGateway.CoordTranslator[coordTranslator]
  end
  H3RoutingPlatformApiGateway.RouteHandler -. "Loads from" .-> H3RoutingPlatformApiGateway.DatasetRegistry
  H3RoutingPlatformApiGateway.RouteHandler -. "Uses" .-> H3RoutingPlatformApiGateway.CoordTranslator
`;case"shortcutPhases":return`---
title: "Shortcut Generator Phases"
---
graph TB
  subgraph H3RoutingPlatformShortcutGenerator["Shortcut Generator"]
    H3RoutingPlatformShortcutGenerator.DataLoader[dataLoader]
    H3RoutingPlatformShortcutGenerator.Phase1[Phase 1: Forward Chunked]
    H3RoutingPlatformShortcutGenerator.CellAssigner[cellAssigner]
    H3RoutingPlatformShortcutGenerator.Phase2[Phase 2: Forward Consolidation]
    H3RoutingPlatformShortcutGenerator.ShortestPathSolver[shortestPathSolver]
    H3RoutingPlatformShortcutGenerator.Phase3[Phase 3: Backward Consolidation]
    H3RoutingPlatformShortcutGenerator.Deduplicator[deduplicator]
    H3RoutingPlatformShortcutGenerator.Phase4[Phase 4: Backward Chunked]
    H3RoutingPlatformShortcutGenerator.Finalizer[finalizer]
  end
  H3RoutingPlatformDuckdb([DuckDB Database])
  H3RoutingPlatformShortcutGenerator.DataLoader -. "Loads edges" .-> H3RoutingPlatformShortcutGenerator.Phase1
  H3RoutingPlatformShortcutGenerator.Phase1 -. "Per iteration" .-> H3RoutingPlatformShortcutGenerator.CellAssigner
  H3RoutingPlatformShortcutGenerator.Phase1 -. "Chunked outputs" .-> H3RoutingPlatformShortcutGenerator.Phase2
  H3RoutingPlatformShortcutGenerator.CellAssigner -. "Active shortcuts" .-> H3RoutingPlatformShortcutGenerator.ShortestPathSolver
  H3RoutingPlatformShortcutGenerator.ShortestPathSolver -. "Optimal paths" .-> H3RoutingPlatformShortcutGenerator.Deduplicator
  H3RoutingPlatformShortcutGenerator.Phase2 -. "Consolidated to res 0" .-> H3RoutingPlatformShortcutGenerator.Phase3
  H3RoutingPlatformShortcutGenerator.Phase3 -. "Re-partitioned" .-> H3RoutingPlatformShortcutGenerator.Phase4
  H3RoutingPlatformShortcutGenerator.Phase4 -. "All resolutions done" .-> H3RoutingPlatformShortcutGenerator.Finalizer
  H3RoutingPlatformShortcutGenerator.Finalizer -. "Writes shortcuts schema" .-> H3RoutingPlatformDuckdb
`;case"duckOSMComponents":return`---
title: "duckOSM Processing Pipeline"
---
graph TB
  subgraph H3RoutingPlatformDuckOSM["duckOSM"]
    H3RoutingPlatformDuckOSM.PbfLoader[pbfLoader]
    H3RoutingPlatformDuckOSM.RoadFilter[roadFilter]
    H3RoutingPlatformDuckOSM.GraphBuilder[graphBuilder]
    H3RoutingPlatformDuckOSM.GraphSimplifier[graphSimplifier]
    H3RoutingPlatformDuckOSM.SpeedProcessor[speedProcessor]
    H3RoutingPlatformDuckOSM.CostCalculator[costCalculator]
    H3RoutingPlatformDuckOSM.RestrictionProcessor[restrictionProcessor]
    H3RoutingPlatformDuckOSM.EdgeGraphBuilder[edgeGraphBuilder]
    H3RoutingPlatformDuckOSM.H3Indexer[h3Indexer]
  end
  H3RoutingPlatformDuckOSM.PbfLoader -. "Flows to" .-> H3RoutingPlatformDuckOSM.RoadFilter
  H3RoutingPlatformDuckOSM.RoadFilter -. "Flows to" .-> H3RoutingPlatformDuckOSM.GraphBuilder
  H3RoutingPlatformDuckOSM.GraphBuilder -. "Flows to" .-> H3RoutingPlatformDuckOSM.GraphSimplifier
  H3RoutingPlatformDuckOSM.GraphSimplifier -. "Flows to" .-> H3RoutingPlatformDuckOSM.SpeedProcessor
  H3RoutingPlatformDuckOSM.SpeedProcessor -. "Flows to" .-> H3RoutingPlatformDuckOSM.CostCalculator
  H3RoutingPlatformDuckOSM.CostCalculator -. "Flows to" .-> H3RoutingPlatformDuckOSM.RestrictionProcessor
  H3RoutingPlatformDuckOSM.RestrictionProcessor -. "Flows to" .-> H3RoutingPlatformDuckOSM.EdgeGraphBuilder
  H3RoutingPlatformDuckOSM.EdgeGraphBuilder -. "Flows to" .-> H3RoutingPlatformDuckOSM.H3Indexer
`;case"routingSequence":return`---
title: "Routing Request Sequence"
---
graph TB
  Developer[fa:fa-user Developer]
  subgraph H3RoutingPlatform["H3 Routing Platform"]
    H3RoutingPlatform.StreamlitUI[Streamlit UI]
    subgraph H3RoutingPlatform.ApiGateway["API Gateway"]
      H3RoutingPlatform.ApiGateway.RouteHandler[routeHandler]
      H3RoutingPlatform.ApiGateway.DatasetRegistry[datasetRegistry]
      H3RoutingPlatform.ApiGateway.CoordTranslator[coordTranslator]
    end
    subgraph H3RoutingPlatform.CppEngine["C++ Routing Engine"]
      H3RoutingPlatform.CppEngine.QueryAlgorithms[queryAlgorithms]
      H3RoutingPlatform.CppEngine.SpatialIndex[spatialIndex]
      H3RoutingPlatform.CppEngine.CsrGraph[csrGraph]
      H3RoutingPlatform.CppEngine.PathExpander[pathExpander]
      H3RoutingPlatform.CppEngine.ShortcutGraph[shortcutGraph]
    end
  end
  Developer -. "Uses for visualization" .-> H3RoutingPlatform.StreamlitUI
  H3RoutingPlatform.ApiGateway.RouteHandler -. "Loads from" .-> H3RoutingPlatform.ApiGateway.DatasetRegistry
  H3RoutingPlatform.ApiGateway.RouteHandler -. "Uses" .-> H3RoutingPlatform.ApiGateway.CoordTranslator
  H3RoutingPlatform.CppEngine.QueryAlgorithms -. "Queries" .-> H3RoutingPlatform.CppEngine.ShortcutGraph
  H3RoutingPlatform.CppEngine.SpatialIndex -. "Indexes edges" .-> H3RoutingPlatform.CppEngine.ShortcutGraph
  H3RoutingPlatform.CppEngine.QueryAlgorithms -. "Queries" .-> H3RoutingPlatform.CppEngine.CsrGraph
  H3RoutingPlatform.CppEngine.QueryAlgorithms -. "Expands shortcuts" .-> H3RoutingPlatform.CppEngine.PathExpander
  H3RoutingPlatform.StreamlitUI -. "HTTP requests" .-> H3RoutingPlatform.ApiGateway
  H3RoutingPlatform.ApiGateway -. "Route queries (port 8082)" .-> H3RoutingPlatform.CppEngine
`;default:throw new Error("Unknown viewId: "+t)}}export{o as mmdSource};
