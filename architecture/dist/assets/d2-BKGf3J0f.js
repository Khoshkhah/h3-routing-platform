function t(n){switch(n){case"index":return`direction: down

Developer: {
  label: "Developer"
  shape: person
}
ExternalClient: {
  label: "External Client"
  shape: person
}
H3RoutingPlatform: {
  label: "H3 Routing Platform"
}

Developer -> H3RoutingPlatform: "[...]"
ExternalClient -> H3RoutingPlatform: "REST API calls"
`;case"containerView":return`direction: down

Developer: {
  label: "Developer"
  shape: person
}
ExternalClient: {
  label: "External Client"
  shape: person
}
H3RoutingPlatform: {
  label: "H3 Routing Platform"

  StreamlitUI: {
    label: "Streamlit UI"
  }
  PythonSDK: {
    label: "Python SDK"
  }
  OsmData: {
    label: "OpenStreetMap PBF"
    shape: stored_data
  }
  H3Toolkit: {
    label: "H3 Toolkit"
  }
  ApiGateway: {
    label: "API Gateway"
  }
  DuckOSM: {
    label: "duckOSM"
  }
  ShortcutGenerator: {
    label: "Shortcut Generator"
  }
  Duckdb: {
    label: "DuckDB Database"
    shape: stored_data
  }
  CppEngine: {
    label: "C++ Routing Engine"
  }
}

Developer -> H3RoutingPlatform.StreamlitUI: "Uses for visualization"
Developer -> H3RoutingPlatform.PythonSDK: "Integrates via"
ExternalClient -> H3RoutingPlatform.ApiGateway: "REST API calls"
H3RoutingPlatform.StreamlitUI -> H3RoutingPlatform.ApiGateway: "HTTP requests"
H3RoutingPlatform.ApiGateway -> H3RoutingPlatform.CppEngine: "Route queries (port 8082)"
H3RoutingPlatform.PythonSDK -> H3RoutingPlatform.ApiGateway: "HTTP requests"
H3RoutingPlatform.Duckdb -> H3RoutingPlatform.CppEngine: "Loads at startup"
H3RoutingPlatform.DuckOSM -> H3RoutingPlatform.Duckdb: "Creates road graph"
H3RoutingPlatform.OsmData -> H3RoutingPlatform.DuckOSM: "Input"
H3RoutingPlatform.ShortcutGenerator -> H3RoutingPlatform.Duckdb: "Writes shortcuts"
H3RoutingPlatform.H3Toolkit -> H3RoutingPlatform.ShortcutGenerator: "H3 utilities"
H3RoutingPlatform.Duckdb -> H3RoutingPlatform.ShortcutGenerator: "Input edges"
`;case"dataPipeline":return`direction: down

H3RoutingPlatformOsmData: {
  label: "OpenStreetMap PBF"
  shape: stored_data
}
H3RoutingPlatformH3Toolkit: {
  label: "H3 Toolkit"
}
H3RoutingPlatformDuckOSM: {
  label: "duckOSM"
}
H3RoutingPlatformDuckdb: {
  label: "DuckDB Database"
  shape: stored_data
}
H3RoutingPlatformShortcutGenerator: {
  label: "Shortcut Generator"

  Phase1: {
    label: "phase1"
  }
  Phase2: {
    label: "phase2"
  }
  Phase3: {
    label: "phase3"
  }
  Phase4: {
    label: "phase4"
  }
}

H3RoutingPlatformOsmData -> H3RoutingPlatformDuckOSM: "Input"
H3RoutingPlatformDuckOSM -> H3RoutingPlatformDuckdb: "Creates road graph"
H3RoutingPlatformShortcutGenerator.Phase1 -> H3RoutingPlatformShortcutGenerator.Phase2: "Flows to"
H3RoutingPlatformShortcutGenerator.Phase2 -> H3RoutingPlatformShortcutGenerator.Phase3: "Flows to"
H3RoutingPlatformShortcutGenerator.Phase3 -> H3RoutingPlatformShortcutGenerator.Phase4: "Flows to"
H3RoutingPlatformDuckdb -> H3RoutingPlatformShortcutGenerator: "Input edges"
H3RoutingPlatformShortcutGenerator -> H3RoutingPlatformDuckdb: "Writes shortcuts"
H3RoutingPlatformH3Toolkit -> H3RoutingPlatformShortcutGenerator: "H3 utilities"
`;case"runtimeFlow":return`direction: down

Developer: {
  label: "Developer"
  shape: person
}
ExternalClient: {
  label: "External Client"
  shape: person
}
H3RoutingPlatform: {
  label: "H3 Routing Platform"

  StreamlitUI: {
    label: "Streamlit UI"
  }
  PythonSDK: {
    label: "Python SDK"
  }
  Duckdb: {
    label: "DuckDB Database"
    shape: stored_data
  }
  ApiGateway: {
    label: "API Gateway"
  }
  CppEngine: {
    label: "C++ Routing Engine"
  }
}

Developer -> H3RoutingPlatform.StreamlitUI: "Uses for visualization"
Developer -> H3RoutingPlatform.PythonSDK: "Integrates via"
ExternalClient -> H3RoutingPlatform.ApiGateway: "REST API calls"
H3RoutingPlatform.StreamlitUI -> H3RoutingPlatform.ApiGateway: "HTTP requests"
H3RoutingPlatform.PythonSDK -> H3RoutingPlatform.ApiGateway: "HTTP requests"
H3RoutingPlatform.ApiGateway -> H3RoutingPlatform.CppEngine: "Route queries (port 8082)"
H3RoutingPlatform.Duckdb -> H3RoutingPlatform.CppEngine: "Loads at startup"
`;case"engineComponents":return`direction: down

H3RoutingPlatformCppEngine: {
  label: "C++ Routing Engine"

  QueryAlgorithms: {
    label: "queryAlgorithms"
  }
  SpatialIndex: {
    label: "spatialIndex"
  }
  CsrGraph: {
    label: "csrGraph"
  }
  PathExpander: {
    label: "pathExpander"
  }
  ShortcutGraph: {
    label: "shortcutGraph"
  }
}

H3RoutingPlatformCppEngine.QueryAlgorithms -> H3RoutingPlatformCppEngine.ShortcutGraph: "Queries"
H3RoutingPlatformCppEngine.SpatialIndex -> H3RoutingPlatformCppEngine.ShortcutGraph: "Indexes edges"
H3RoutingPlatformCppEngine.QueryAlgorithms -> H3RoutingPlatformCppEngine.CsrGraph: "Queries"
H3RoutingPlatformCppEngine.QueryAlgorithms -> H3RoutingPlatformCppEngine.PathExpander: "Expands shortcuts"
`;case"apiGatewayComponents":return`direction: down

H3RoutingPlatformApiGateway: {
  label: "API Gateway"

  RouteHandler: {
    label: "routeHandler"
  }
  DatasetRegistry: {
    label: "datasetRegistry"
  }
  CoordTranslator: {
    label: "coordTranslator"
  }
}

H3RoutingPlatformApiGateway.RouteHandler -> H3RoutingPlatformApiGateway.DatasetRegistry: "Loads from"
H3RoutingPlatformApiGateway.RouteHandler -> H3RoutingPlatformApiGateway.CoordTranslator: "Uses"
`;case"shortcutPhases":return`direction: down

H3RoutingPlatformShortcutGenerator: {
  label: "Shortcut Generator"

  Phase1: {
    label: "phase1"
  }
  Phase2: {
    label: "phase2"
  }
  Phase3: {
    label: "phase3"
  }
  Phase4: {
    label: "phase4"
  }
}

H3RoutingPlatformShortcutGenerator.Phase1 -> H3RoutingPlatformShortcutGenerator.Phase2: "Flows to"
H3RoutingPlatformShortcutGenerator.Phase2 -> H3RoutingPlatformShortcutGenerator.Phase3: "Flows to"
H3RoutingPlatformShortcutGenerator.Phase3 -> H3RoutingPlatformShortcutGenerator.Phase4: "Flows to"
`;default:throw new Error("Unknown viewId: "+n)}}export{t as d2Source};
