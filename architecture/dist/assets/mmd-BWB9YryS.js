function n(t){switch(t){case"index":return`---
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
  H3RoutingPlatformDuckdb([DuckDB Database])
  subgraph H3RoutingPlatformShortcutGenerator["Shortcut Generator"]
    H3RoutingPlatformShortcutGenerator.Phase1[phase1]
    H3RoutingPlatformShortcutGenerator.Phase2[phase2]
    H3RoutingPlatformShortcutGenerator.Phase3[phase3]
    H3RoutingPlatformShortcutGenerator.Phase4[phase4]
  end
  H3RoutingPlatformOsmData -. "Input" .-> H3RoutingPlatformDuckOSM
  H3RoutingPlatformDuckOSM -. "Creates road graph" .-> H3RoutingPlatformDuckdb
  H3RoutingPlatformShortcutGenerator.Phase1 -. "Flows to" .-> H3RoutingPlatformShortcutGenerator.Phase2
  H3RoutingPlatformShortcutGenerator.Phase2 -. "Flows to" .-> H3RoutingPlatformShortcutGenerator.Phase3
  H3RoutingPlatformShortcutGenerator.Phase3 -. "Flows to" .-> H3RoutingPlatformShortcutGenerator.Phase4
  H3RoutingPlatformDuckdb -. "Input edges" .-> H3RoutingPlatformShortcutGenerator
  H3RoutingPlatformShortcutGenerator -. "Writes shortcuts" .-> H3RoutingPlatformDuckdb
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
    H3RoutingPlatformShortcutGenerator.Phase1[phase1]
    H3RoutingPlatformShortcutGenerator.Phase2[phase2]
    H3RoutingPlatformShortcutGenerator.Phase3[phase3]
    H3RoutingPlatformShortcutGenerator.Phase4[phase4]
  end
  H3RoutingPlatformShortcutGenerator.Phase1 -. "Flows to" .-> H3RoutingPlatformShortcutGenerator.Phase2
  H3RoutingPlatformShortcutGenerator.Phase2 -. "Flows to" .-> H3RoutingPlatformShortcutGenerator.Phase3
  H3RoutingPlatformShortcutGenerator.Phase3 -. "Flows to" .-> H3RoutingPlatformShortcutGenerator.Phase4
`;default:throw new Error("Unknown viewId: "+t)}}export{n as mmdSource};
