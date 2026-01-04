function t(e){switch(e){case"index":return`digraph {
    graph [TBbalance=min,
        bgcolor=transparent,
        compound=true,
        fontname=Arial,
        fontsize=20,
        labeljust=l,
        labelloc=t,
        layout=dot,
        likec4_viewId=index,
        nodesep=1.528,
        outputorder=nodesfirst,
        pad=0.209,
        rankdir=TB,
        ranksep=1.667,
        splines=spline
    ];
    node [color="#2563eb",
        fillcolor="#3b82f6",
        fontcolor="#eff6ff",
        fontname=Arial,
        label="\\N",
        penwidth=0,
        shape=rect,
        style=filled
    ];
    edge [arrowsize=0.75,
        color="#8D8D8D",
        fontcolor="#C9C9C9",
        fontname=Arial,
        fontsize=14,
        penwidth=2
    ];
    developer [color="#7E451D",
        fillcolor="#A35829",
        fontcolor="#FFE0C2",
        height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Developer</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#f9b27c">Uses Streamlit UI for testing and Python SDK<BR/>for integration</FONT></TD></TR></TABLE>>,
        likec4_id=developer,
        likec4_level=0,
        margin="0.223,0.223",
        width=4.445];
    h3routingplatform [color="#0369a1",
        fillcolor="#0284c7",
        fontcolor="#f0f9ff",
        height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">H3 Routing Platform</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#B6ECF7">High-performance H3-indexed Contraction<BR/>Hierarchy routing engine</FONT></TD></TR></TABLE>>,
        likec4_id=h3RoutingPlatform,
        likec4_level=0,
        margin="0.223,0.223",
        width=4.445];
    developer -> h3routingplatform [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14"><B>[...]</B></FONT></TD></TR></TABLE>>,
        likec4_id=z8ltus,
        minlen=1,
        style=dashed];
    externalclient [color="#7E451D",
        fillcolor="#A35829",
        fontcolor="#FFE0C2",
        height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">External Client</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#f9b27c">Any application consuming the routing REST<BR/>API</FONT></TD></TR></TABLE>>,
        likec4_id=externalClient,
        likec4_level=0,
        margin="0.223,0.223",
        width=4.445];
    externalclient -> h3routingplatform [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">REST API calls</FONT></TD></TR></TABLE>>,
        likec4_id=xdxkmu,
        minlen=1,
        style=dashed];
}
`;case"containerView":return`digraph {
    graph [TBbalance=min,
        bgcolor=transparent,
        compound=true,
        fontname=Arial,
        fontsize=20,
        labeljust=l,
        labelloc=t,
        layout=dot,
        likec4_viewId=containerView,
        nodesep=1.528,
        outputorder=nodesfirst,
        pad=0.209,
        rankdir=TB,
        ranksep=1.667,
        splines=spline
    ];
    node [color="#2563eb",
        fillcolor="#3b82f6",
        fontcolor="#eff6ff",
        fontname=Arial,
        label="\\N",
        penwidth=0,
        shape=rect,
        style=filled
    ];
    edge [arrowsize=0.75,
        color="#8D8D8D",
        fontcolor="#C9C9C9",
        fontname=Arial,
        fontsize=14,
        penwidth=2
    ];
    subgraph cluster_h3routingplatform {
        graph [color="#0b3c57",
            fillcolor="#0d4b6c",
            label=<<FONT POINT-SIZE="11" COLOR="#b6ecf7b3"><B>H3 ROUTING PLATFORM</B></FONT>>,
            likec4_depth=1,
            likec4_id=h3RoutingPlatform,
            likec4_level=0,
            margin=40,
            style=filled
        ];
        streamlitui [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Streamlit UI</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">Python / Streamlit</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Interactive map visualization and debugging<BR/>interface</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.streamlitUI",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        pythonsdk [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Python SDK</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">Python</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">h3-routing-client package for programmatic<BR/>access</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.pythonSDK",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        osmdata [color="#475569",
            fillcolor="#64748b",
            fontcolor="#f8fafc",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">OpenStreetMap PBF</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#cbd5e1">Raw map data source</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.osmData",
            likec4_level=1,
            margin="0.223,0",
            penwidth=2,
            shape=cylinder,
            width=4.445];
        h3toolkit [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">H3 Toolkit</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">C++ / Python</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Shared H3 spatial utilities library</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.h3Toolkit",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        apigateway [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">API Gateway</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">Python / FastAPI</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">REST API on port 8000, coordinates dataset<BR/>loading and request translation</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.apiGateway",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        duckosm [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">duckOSM</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">Python / DuckDB</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Converts OpenStreetMap PBF files to road<BR/>network in DuckDB</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.duckOSM",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        shortcutgenerator [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Shortcut Generator</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">Python / DuckDB</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">4-phase H3 hierarchy processor for<BR/>contraction shortcuts</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.shortcutGenerator",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        duckdb [color="#475569",
            fillcolor="#64748b",
            fontcolor="#f8fafc",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">DuckDB Database</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#cbd5e1">Stores edges, nodes, shortcuts, and dataset<BR/>info</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.duckdb",
            likec4_level=1,
            margin="0.223,0",
            penwidth=2,
            shape=cylinder,
            width=4.445];
        cppengine [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">C++ Routing Engine</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">C++ / Crow HTTP</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">High-performance engine on port 8082 with CH<BR/>algorithms</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.cppEngine",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
    }
    developer [color="#7E451D",
        fillcolor="#A35829",
        fontcolor="#FFE0C2",
        height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Developer</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#f9b27c">Uses Streamlit UI for testing and Python SDK<BR/>for integration</FONT></TD></TR></TABLE>>,
        likec4_id=developer,
        likec4_level=0,
        margin="0.223,0.223",
        width=4.445];
    developer -> streamlitui [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Uses for visualization</FONT></TD></TR></TABLE>>,
        likec4_id="1e5blbv",
        style=dashed];
    developer -> pythonsdk [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Integrates via</FONT></TD></TR></TABLE>>,
        likec4_id=dbr3vm,
        style=dashed];
    externalclient [color="#7E451D",
        fillcolor="#A35829",
        fontcolor="#FFE0C2",
        height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">External Client</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#f9b27c">Any application consuming the routing REST<BR/>API</FONT></TD></TR></TABLE>>,
        likec4_id=externalClient,
        likec4_level=0,
        margin="0.223,0.223",
        width=4.445];
    externalclient -> apigateway [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">REST API calls</FONT></TD></TR></TABLE>>,
        likec4_id=u1zf14,
        minlen=1,
        style=dashed];
    streamlitui -> apigateway [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">HTTP requests</FONT></TD></TR></TABLE>>,
        likec4_id="1in9qsb",
        style=dashed,
        weight=2];
    pythonsdk -> apigateway [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">HTTP requests</FONT></TD></TR></TABLE>>,
        likec4_id="1krgheq",
        style=dashed,
        weight=2];
    osmdata -> duckosm [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Input</FONT></TD></TR></TABLE>>,
        likec4_id=lfwsn7,
        minlen=1,
        style=dashed];
    h3toolkit -> shortcutgenerator [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">H3 utilities</FONT></TD></TR></TABLE>>,
        likec4_id=kdf97g,
        minlen=1,
        style=dashed];
    apigateway -> cppengine [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Route queries (port 8082)</FONT></TD></TR></TABLE>>,
        likec4_id=zp2xqf,
        style=dashed,
        weight=2];
    duckosm -> duckdb [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Creates road graph</FONT></TD></TR></TABLE>>,
        likec4_id=vus74t,
        style=dashed];
    shortcutgenerator -> duckdb [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Writes shortcuts</FONT></TD></TR></TABLE>>,
        likec4_id="1otwa5y",
        style=dashed];
    duckdb -> shortcutgenerator [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Input edges</FONT></TD></TR></TABLE>>,
        likec4_id="1mxapjq",
        style=dashed];
    duckdb -> cppengine [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Loads at startup</FONT></TD></TR></TABLE>>,
        likec4_id="1l1d1rs",
        style=dashed];
}
`;case"dataPipeline":return`digraph {
    graph [TBbalance=min,
        bgcolor=transparent,
        compound=true,
        fontname=Arial,
        fontsize=20,
        labeljust=l,
        labelloc=t,
        layout=dot,
        likec4_viewId=dataPipeline,
        nodesep=1.528,
        outputorder=nodesfirst,
        pad=0.209,
        rankdir=TB,
        ranksep=1.667,
        splines=spline
    ];
    node [color="#2563eb",
        fillcolor="#3b82f6",
        fontcolor="#eff6ff",
        fontname=Arial,
        penwidth=0,
        shape=rect,
        style=filled
    ];
    edge [arrowsize=0.75,
        color="#8D8D8D",
        fontcolor="#C9C9C9",
        fontname=Arial,
        fontsize=14,
        penwidth=2
    ];
    subgraph cluster_shortcutgenerator {
        graph [color="#1b3d88",
            fillcolor="#194b9e",
            label=<<FONT POINT-SIZE="11" COLOR="#bfdbfeb3"><B>SHORTCUT GENERATOR</B></FONT>>,
            likec4_depth=1,
            likec4_id="h3RoutingPlatform.shortcutGenerator",
            likec4_level=0,
            margin=40,
            style=filled
        ];
        dataloader [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">dataLoader</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Loads edges and edge_graph from DuckDB into<BR/>working tables</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.shortcutGenerator.dataLoader",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        phase1 [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Phase 1: Forward Chunked</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Processes res 15→7 in parallel chunks per<BR/>partition cell</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.shortcutGenerator.phase1",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        cellassigner [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">cellAssigner</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Assigns shortcuts to H3 cells based on LCA<BR/>resolution</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.shortcutGenerator.cellAssigner",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        phase2 [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Phase 2: Forward Consolidation</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Merges cells upward res 6→0, deduplicating<BR/>via cost</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.shortcutGenerator.phase2",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        shortestpathsolver [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">shortestPathSolver</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Computes optimal shortcuts via SciPy/DuckDB<BR/>graph algorithms</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.shortcutGenerator.shortestPathSolver",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        phase3 [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Phase 3: Backward Consolidation</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Splits cells downward res 0→7,<BR/>re-partitioning shortcuts</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.shortcutGenerator.phase3",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        deduplicator [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">deduplicator</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Removes redundant shortcuts keeping minimum<BR/>cost</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.shortcutGenerator.deduplicator",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        phase4 [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Phase 4: Backward Chunked</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Processes res 8→15 in parallel chunks,<BR/>finalizing all resolutions</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.shortcutGenerator.phase4",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        finalizer [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">finalizer</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Exports final shortcuts to Parquet and DuckDB<BR/>schema</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.shortcutGenerator.finalizer",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
    }
    osmdata [color="#475569",
        fillcolor="#64748b",
        fontcolor="#f8fafc",
        height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">OpenStreetMap PBF</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#cbd5e1">Raw map data source</FONT></TD></TR></TABLE>>,
        likec4_id="h3RoutingPlatform.osmData",
        likec4_level=0,
        margin="0.223,0",
        penwidth=2,
        shape=cylinder,
        width=4.445];
    duckosm [height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">duckOSM</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">Python / DuckDB</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Converts OpenStreetMap PBF files to road<BR/>network in DuckDB</FONT></TD></TR></TABLE>>,
        likec4_id="h3RoutingPlatform.duckOSM",
        likec4_level=0,
        margin="0.223,0.223",
        width=4.445];
    osmdata -> duckosm [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Input</FONT></TD></TR></TABLE>>,
        likec4_id=lfwsn7,
        minlen=1,
        style=dashed];
    h3toolkit [height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">H3 Toolkit</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">C++ / Python</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Shared H3 spatial utilities library</FONT></TD></TR></TABLE>>,
        likec4_id="h3RoutingPlatform.h3Toolkit",
        likec4_level=0,
        margin="0.223,0.223",
        width=4.445];
    h3toolkit -> dataloader [arrowhead=normal,
        lhead=cluster_shortcutgenerator,
        likec4_id=kdf97g,
        minlen=1,
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">H3 utilities</FONT></TD></TR></TABLE>>];
    duckdb [color="#475569",
        fillcolor="#64748b",
        fontcolor="#f8fafc",
        height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">DuckDB Database</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#cbd5e1">Stores edges, nodes, shortcuts, and dataset<BR/>info</FONT></TD></TR></TABLE>>,
        likec4_id="h3RoutingPlatform.duckdb",
        likec4_level=0,
        margin="0.223,0",
        penwidth=2,
        shape=cylinder,
        width=4.445];
    duckosm -> duckdb [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Creates road graph</FONT></TD></TR></TABLE>>,
        likec4_id=vus74t,
        style=dashed,
        weight=2];
    dataloader -> phase1 [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Loads edges</FONT></TD></TR></TABLE>>,
        likec4_id=uuojg5,
        style=dashed];
    phase1 -> cellassigner [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Per iteration</FONT></TD></TR></TABLE>>,
        likec4_id="1bieqxw",
        style=dashed];
    phase1 -> phase2 [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Chunked outputs</FONT></TD></TR></TABLE>>,
        likec4_id="6ez1wp",
        style=dashed];
    cellassigner -> shortestpathsolver [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Active shortcuts</FONT></TD></TR></TABLE>>,
        likec4_id="1bfpz6e",
        style=dashed];
    phase2 -> phase3 [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Consolidated to res 0</FONT></TD></TR></TABLE>>,
        likec4_id=geqf2j,
        style=dashed];
    shortestpathsolver -> deduplicator [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Optimal paths</FONT></TD></TR></TABLE>>,
        likec4_id="1mm0d2g",
        minlen=1,
        style=dashed];
    phase3 -> phase4 [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Re-partitioned</FONT></TD></TR></TABLE>>,
        likec4_id="1f6kz71",
        style=dashed];
    phase4 -> finalizer [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">All resolutions done</FONT></TD></TR></TABLE>>,
        likec4_id=qy7p3t,
        style=dashed,
        weight=2];
    finalizer -> duckdb [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Writes shortcuts schema</FONT></TD></TR></TABLE>>,
        likec4_id="1fgho34",
        style=dashed];
}
`;case"runtimeFlow":return`digraph {
    graph [TBbalance=min,
        bgcolor=transparent,
        compound=true,
        fontname=Arial,
        fontsize=20,
        labeljust=l,
        labelloc=t,
        layout=dot,
        likec4_viewId=runtimeFlow,
        nodesep=1.528,
        outputorder=nodesfirst,
        pad=0.209,
        rankdir=TB,
        ranksep=1.667,
        splines=spline
    ];
    node [color="#2563eb",
        fillcolor="#3b82f6",
        fontcolor="#eff6ff",
        fontname=Arial,
        penwidth=0,
        shape=rect,
        style=filled
    ];
    edge [arrowsize=0.75,
        color="#8D8D8D",
        fontcolor="#C9C9C9",
        fontname=Arial,
        fontsize=14,
        penwidth=2
    ];
    subgraph cluster_h3routingplatform {
        graph [color="#0b3c57",
            fillcolor="#0d4b6c",
            label=<<FONT POINT-SIZE="11" COLOR="#b6ecf7b3"><B>H3 ROUTING PLATFORM</B></FONT>>,
            likec4_depth=1,
            likec4_id=h3RoutingPlatform,
            likec4_level=0,
            margin=40,
            style=filled
        ];
        streamlitui [group=h3RoutingPlatform,
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Streamlit UI</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">Python / Streamlit</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Interactive map visualization and debugging<BR/>interface</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.streamlitUI",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        pythonsdk [group=h3RoutingPlatform,
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Python SDK</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">Python</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">h3-routing-client package for programmatic<BR/>access</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.pythonSDK",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        duckdb [color="#475569",
            fillcolor="#64748b",
            fontcolor="#f8fafc",
            group=h3RoutingPlatform,
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">DuckDB Database</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#cbd5e1">Stores edges, nodes, shortcuts, and dataset<BR/>info</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.duckdb",
            likec4_level=1,
            margin="0.223,0",
            penwidth=2,
            shape=cylinder,
            width=4.445];
        apigateway [group=h3RoutingPlatform,
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">API Gateway</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">Python / FastAPI</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">REST API on port 8000, coordinates dataset<BR/>loading and request translation</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.apiGateway",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        cppengine [group=h3RoutingPlatform,
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">C++ Routing Engine</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">C++ / Crow HTTP</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">High-performance engine on port 8082 with CH<BR/>algorithms</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.cppEngine",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
    }
    developer [color="#7E451D",
        fillcolor="#A35829",
        fontcolor="#FFE0C2",
        height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Developer</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#f9b27c">Uses Streamlit UI for testing and Python SDK<BR/>for integration</FONT></TD></TR></TABLE>>,
        likec4_id=developer,
        likec4_level=0,
        margin="0.223,0.223",
        width=4.445];
    developer -> streamlitui [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Uses for visualization</FONT></TD></TR></TABLE>>,
        likec4_id="1e5blbv",
        style=dashed];
    developer -> pythonsdk [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Integrates via</FONT></TD></TR></TABLE>>,
        likec4_id=dbr3vm,
        style=dashed];
    externalclient [color="#7E451D",
        fillcolor="#A35829",
        fontcolor="#FFE0C2",
        height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">External Client</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#f9b27c">Any application consuming the routing REST<BR/>API</FONT></TD></TR></TABLE>>,
        likec4_id=externalClient,
        likec4_level=0,
        margin="0.223,0.223",
        width=4.445];
    externalclient -> apigateway [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">REST API calls</FONT></TD></TR></TABLE>>,
        likec4_id=u1zf14,
        minlen=1,
        style=dashed];
    streamlitui -> apigateway [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">HTTP requests</FONT></TD></TR></TABLE>>,
        likec4_id="1in9qsb",
        style=dashed,
        weight=2];
    pythonsdk -> apigateway [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">HTTP requests</FONT></TD></TR></TABLE>>,
        likec4_id="1krgheq",
        style=dashed,
        weight=2];
    duckdb -> cppengine [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Loads at startup</FONT></TD></TR></TABLE>>,
        likec4_id="1l1d1rs",
        minlen=1,
        style=dashed];
    apigateway -> cppengine [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Route queries (port 8082)</FONT></TD></TR></TABLE>>,
        likec4_id=zp2xqf,
        style=dashed,
        weight=2];
}
`;case"engineComponents":return`digraph {
    graph [TBbalance=min,
        bgcolor=transparent,
        compound=true,
        fontname=Arial,
        fontsize=20,
        labeljust=l,
        labelloc=t,
        layout=dot,
        likec4_viewId=engineComponents,
        nodesep=1.528,
        outputorder=nodesfirst,
        pad=0.209,
        rankdir=TB,
        ranksep=1.667,
        splines=spline
    ];
    node [color="#2563eb",
        fillcolor="#3b82f6",
        fontcolor="#eff6ff",
        fontname=Arial,
        penwidth=0,
        shape=rect,
        style=filled
    ];
    edge [arrowsize=0.75,
        color="#8D8D8D",
        fontcolor="#C9C9C9",
        fontname=Arial,
        fontsize=14,
        penwidth=2
    ];
    subgraph cluster_cppengine {
        graph [color="#1b3d88",
            fillcolor="#194b9e",
            label=<<FONT POINT-SIZE="11" COLOR="#bfdbfeb3"><B>C++ ROUTING ENGINE</B></FONT>>,
            likec4_depth=1,
            likec4_id="h3RoutingPlatform.cppEngine",
            likec4_level=0,
            margin=40,
            style=filled
        ];
        queryalgorithms [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            group="h3RoutingPlatform.cppEngine",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">queryAlgorithms</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Dijkstra, Bidirectional, Pruned,<BR/>Unidirectional CH</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.cppEngine.queryAlgorithms",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        spatialindex [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            group="h3RoutingPlatform.cppEngine",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">spatialIndex</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">H3 or R-tree index for nearest edge lookup</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.cppEngine.spatialIndex",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        csrgraph [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            group="h3RoutingPlatform.cppEngine",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">csrGraph</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Compressed Sparse Row graph for memory<BR/>efficiency</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.cppEngine.csrGraph",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        pathexpander [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            group="h3RoutingPlatform.cppEngine",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">pathExpander</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Resolves shortcut paths to base edge<BR/>sequences</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.cppEngine.pathExpander",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        shortcutgraph [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            group="h3RoutingPlatform.cppEngine",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">shortcutGraph</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Graph with adjacency lists, shortcuts, and<BR/>edge metadata</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.cppEngine.shortcutGraph",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
    }
    queryalgorithms -> csrgraph [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Queries</FONT></TD></TR></TABLE>>,
        likec4_id=ai2pea,
        minlen=1,
        style=dashed];
    queryalgorithms -> pathexpander [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Expands shortcuts</FONT></TD></TR></TABLE>>,
        likec4_id="1maacps",
        minlen=1,
        style=dashed];
    queryalgorithms -> shortcutgraph [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Queries</FONT></TD></TR></TABLE>>,
        likec4_id=g32vts,
        style=dashed];
    spatialindex -> shortcutgraph [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Indexes edges</FONT></TD></TR></TABLE>>,
        likec4_id="11z7ybe",
        minlen=1,
        style=dashed];
}
`;case"apiGatewayComponents":return`digraph {
    graph [TBbalance=min,
        bgcolor=transparent,
        compound=true,
        fontname=Arial,
        fontsize=20,
        labeljust=l,
        labelloc=t,
        layout=dot,
        likec4_viewId=apiGatewayComponents,
        nodesep=1.528,
        outputorder=nodesfirst,
        pad=0.209,
        rankdir=TB,
        ranksep=1.667,
        splines=spline
    ];
    node [color="#2563eb",
        fillcolor="#3b82f6",
        fontcolor="#eff6ff",
        fontname=Arial,
        penwidth=0,
        shape=rect,
        style=filled
    ];
    edge [arrowsize=0.75,
        color="#8D8D8D",
        fontcolor="#C9C9C9",
        fontname=Arial,
        fontsize=14,
        penwidth=2
    ];
    subgraph cluster_apigateway {
        graph [color="#1b3d88",
            fillcolor="#194b9e",
            label=<<FONT POINT-SIZE="11" COLOR="#bfdbfeb3"><B>API GATEWAY</B></FONT>>,
            likec4_depth=1,
            likec4_id="h3RoutingPlatform.apiGateway",
            likec4_level=0,
            margin=40,
            style=filled
        ];
        routehandler [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            group="h3RoutingPlatform.apiGateway",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">routeHandler</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Validates requests and forwards to C++ engine</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.apiGateway.routeHandler",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        datasetregistry [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            group="h3RoutingPlatform.apiGateway",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">datasetRegistry</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Manages available datasets from datasets.yaml</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.apiGateway.datasetRegistry",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        coordtranslator [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            group="h3RoutingPlatform.apiGateway",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">coordTranslator</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Converts lat/lon to graph edge IDs via<BR/>spatial index</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.apiGateway.coordTranslator",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
    }
    routehandler -> datasetregistry [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Loads from</FONT></TD></TR></TABLE>>,
        likec4_id="1hnai0c",
        minlen=1,
        style=dashed];
    routehandler -> coordtranslator [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Uses</FONT></TD></TR></TABLE>>,
        likec4_id="4dg36o",
        minlen=1,
        style=dashed];
}
`;case"shortcutPhases":return`digraph {
    graph [TBbalance=min,
        bgcolor=transparent,
        compound=true,
        fontname=Arial,
        fontsize=20,
        labeljust=l,
        labelloc=t,
        layout=dot,
        likec4_viewId=shortcutPhases,
        nodesep=1.528,
        outputorder=nodesfirst,
        pad=0.209,
        rankdir=TB,
        ranksep=1.667,
        splines=spline
    ];
    node [color="#2563eb",
        fillcolor="#3b82f6",
        fontcolor="#eff6ff",
        fontname=Arial,
        penwidth=0,
        shape=rect,
        style=filled
    ];
    edge [arrowsize=0.75,
        color="#8D8D8D",
        fontcolor="#C9C9C9",
        fontname=Arial,
        fontsize=14,
        penwidth=2
    ];
    subgraph cluster_shortcutgenerator {
        graph [color="#1b3d88",
            fillcolor="#194b9e",
            label=<<FONT POINT-SIZE="11" COLOR="#bfdbfeb3"><B>SHORTCUT GENERATOR</B></FONT>>,
            likec4_depth=1,
            likec4_id="h3RoutingPlatform.shortcutGenerator",
            likec4_level=0,
            margin=40,
            style=filled
        ];
        dataloader [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">dataLoader</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Loads edges and edge_graph from DuckDB into<BR/>working tables</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.shortcutGenerator.dataLoader",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        phase1 [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Phase 1: Forward Chunked</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Processes res 15→7 in parallel chunks per<BR/>partition cell</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.shortcutGenerator.phase1",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        cellassigner [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">cellAssigner</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Assigns shortcuts to H3 cells based on LCA<BR/>resolution</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.shortcutGenerator.cellAssigner",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        phase2 [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Phase 2: Forward Consolidation</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Merges cells upward res 6→0, deduplicating<BR/>via cost</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.shortcutGenerator.phase2",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        shortestpathsolver [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">shortestPathSolver</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Computes optimal shortcuts via SciPy/DuckDB<BR/>graph algorithms</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.shortcutGenerator.shortestPathSolver",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        phase3 [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Phase 3: Backward Consolidation</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Splits cells downward res 0→7,<BR/>re-partitioning shortcuts</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.shortcutGenerator.phase3",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        deduplicator [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">deduplicator</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Removes redundant shortcuts keeping minimum<BR/>cost</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.shortcutGenerator.deduplicator",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        phase4 [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Phase 4: Backward Chunked</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Processes res 8→15 in parallel chunks,<BR/>finalizing all resolutions</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.shortcutGenerator.phase4",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        finalizer [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">finalizer</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Exports final shortcuts to Parquet and DuckDB<BR/>schema</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.shortcutGenerator.finalizer",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
    }
    dataloader -> phase1 [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Loads edges</FONT></TD></TR></TABLE>>,
        likec4_id=uuojg5,
        minlen=1,
        style=dashed];
    phase1 -> cellassigner [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Per iteration</FONT></TD></TR></TABLE>>,
        likec4_id="1bieqxw",
        style=dashed];
    phase1 -> phase2 [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Chunked outputs</FONT></TD></TR></TABLE>>,
        likec4_id="6ez1wp",
        style=dashed];
    cellassigner -> shortestpathsolver [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Active shortcuts</FONT></TD></TR></TABLE>>,
        likec4_id="1bfpz6e",
        style=dashed];
    phase2 -> phase3 [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Consolidated to res 0</FONT></TD></TR></TABLE>>,
        likec4_id=geqf2j,
        style=dashed];
    shortestpathsolver -> deduplicator [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Optimal paths</FONT></TD></TR></TABLE>>,
        likec4_id="1mm0d2g",
        minlen=1,
        style=dashed];
    phase3 -> phase4 [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Re-partitioned</FONT></TD></TR></TABLE>>,
        likec4_id="1f6kz71",
        style=dashed];
    phase4 -> finalizer [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">All resolutions done</FONT></TD></TR></TABLE>>,
        likec4_id=qy7p3t,
        style=dashed,
        weight=2];
    duckdb [color="#475569",
        fillcolor="#64748b",
        fontcolor="#f8fafc",
        height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">DuckDB Database</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#cbd5e1">Stores edges, nodes, shortcuts, and dataset<BR/>info</FONT></TD></TR></TABLE>>,
        likec4_id="h3RoutingPlatform.duckdb",
        likec4_level=0,
        margin="0.223,0",
        penwidth=2,
        shape=cylinder,
        width=4.445];
    finalizer -> duckdb [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Writes shortcuts schema</FONT></TD></TR></TABLE>>,
        likec4_id="1fgho34",
        minlen=1,
        style=dashed];
}
`;case"duckOSMComponents":return`digraph {
    graph [TBbalance=min,
        bgcolor=transparent,
        compound=true,
        fontname=Arial,
        fontsize=20,
        labeljust=l,
        labelloc=t,
        layout=dot,
        likec4_viewId=duckOSMComponents,
        nodesep=1.528,
        outputorder=nodesfirst,
        pad=0.209,
        rankdir=TB,
        ranksep=1.667,
        splines=spline
    ];
    node [color="#2563eb",
        fillcolor="#3b82f6",
        fontcolor="#eff6ff",
        fontname=Arial,
        penwidth=0,
        shape=rect,
        style=filled
    ];
    edge [arrowsize=0.75,
        color="#8D8D8D",
        fontcolor="#C9C9C9",
        fontname=Arial,
        fontsize=14,
        penwidth=2
    ];
    subgraph cluster_duckosm {
        graph [color="#1b3d88",
            fillcolor="#194b9e",
            label=<<FONT POINT-SIZE="11" COLOR="#bfdbfeb3"><B>DUCKOSM</B></FONT>>,
            likec4_depth=1,
            likec4_id="h3RoutingPlatform.duckOSM",
            likec4_level=0,
            margin=40,
            style=filled
        ];
        pbfloader [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">pbfLoader</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Loads PBF via ST_READOSM extension</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.duckOSM.pbfLoader",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        roadfilter [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">roadFilter</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Filters ways to highway types only</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.duckOSM.roadFilter",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        graphbuilder [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">graphBuilder</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Creates directed edges from OSM ways</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.duckOSM.graphBuilder",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        graphsimplifier [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">graphSimplifier</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Contracts degree-2 nodes to simplify graph</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.duckOSM.graphSimplifier",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        speedprocessor [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">speedProcessor</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Infers speed limits from highway tags</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.duckOSM.speedProcessor",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        costcalculator [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">costCalculator</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Calculates travel time costs per edge</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.duckOSM.costCalculator",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        restrictionprocessor [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">restrictionProcessor</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Extracts turn restrictions from relations</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.duckOSM.restrictionProcessor",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        edgegraphbuilder [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">edgeGraphBuilder</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Builds edge-to-edge adjacency graph</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.duckOSM.edgeGraphBuilder",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
        h3indexer [color="#4f46e5",
            fillcolor="#6366f1",
            fontcolor="#eef2ff",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">h3Indexer</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Adds H3 cell indexing to edges</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.duckOSM.h3Indexer",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
    }
    pbfloader -> roadfilter [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Flows to</FONT></TD></TR></TABLE>>,
        likec4_id="1nnfuxj",
        minlen=1,
        style=dashed];
    roadfilter -> graphbuilder [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Flows to</FONT></TD></TR></TABLE>>,
        likec4_id="1h9ei1r",
        style=dashed];
    graphbuilder -> graphsimplifier [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Flows to</FONT></TD></TR></TABLE>>,
        likec4_id="5thk7l",
        style=dashed];
    graphsimplifier -> speedprocessor [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Flows to</FONT></TD></TR></TABLE>>,
        likec4_id=fcwb3h,
        style=dashed];
    speedprocessor -> costcalculator [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Flows to</FONT></TD></TR></TABLE>>,
        likec4_id=xe7eto,
        style=dashed];
    costcalculator -> restrictionprocessor [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Flows to</FONT></TD></TR></TABLE>>,
        likec4_id="12is2tb",
        style=dashed];
    restrictionprocessor -> edgegraphbuilder [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Flows to</FONT></TD></TR></TABLE>>,
        likec4_id=m0znl2,
        style=dashed];
    edgegraphbuilder -> h3indexer [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Flows to</FONT></TD></TR></TABLE>>,
        likec4_id="1wn659y",
        minlen=1,
        style=dashed];
}
`;case"routingSequence":return`digraph {
    graph [TBbalance=min,
        bgcolor=transparent,
        compound=true,
        fontname=Arial,
        fontsize=20,
        labeljust=l,
        labelloc=t,
        layout=dot,
        likec4_viewId=routingSequence,
        nodesep=1.528,
        outputorder=nodesfirst,
        pad=0.209,
        rankdir=TB,
        ranksep=1.667,
        splines=spline
    ];
    node [color="#2563eb",
        fillcolor="#3b82f6",
        fontcolor="#eff6ff",
        fontname=Arial,
        penwidth=0,
        shape=rect,
        style=filled
    ];
    edge [arrowsize=0.75,
        color="#8D8D8D",
        fontcolor="#C9C9C9",
        fontname=Arial,
        fontsize=14,
        penwidth=2
    ];
    subgraph cluster_h3routingplatform {
        graph [color="#0d374e",
            fillcolor="#0f4460",
            label=<<FONT POINT-SIZE="11" COLOR="#b6ecf7b3"><B>H3 ROUTING PLATFORM</B></FONT>>,
            likec4_depth=2,
            likec4_id=h3RoutingPlatform,
            likec4_level=0,
            margin=40,
            style=filled
        ];
        subgraph cluster_apigateway {
            graph [color="#1b3d88",
                fillcolor="#194b9e",
                label=<<FONT POINT-SIZE="11" COLOR="#bfdbfeb3"><B>API GATEWAY</B></FONT>>,
                likec4_depth=1,
                likec4_id="h3RoutingPlatform.apiGateway",
                likec4_level=1,
                margin=40,
                style=filled
            ];
            routehandler [color="#4f46e5",
                fillcolor="#6366f1",
                fontcolor="#eef2ff",
                group="h3RoutingPlatform.apiGateway",
                height=2.5,
                label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">routeHandler</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Validates requests and forwards to C++ engine</FONT></TD></TR></TABLE>>,
                likec4_id="h3RoutingPlatform.apiGateway.routeHandler",
                likec4_level=2,
                margin="0.223,0.223",
                width=4.445];
            datasetregistry [color="#4f46e5",
                fillcolor="#6366f1",
                fontcolor="#eef2ff",
                group="h3RoutingPlatform.apiGateway",
                height=2.5,
                label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">datasetRegistry</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Manages available datasets from datasets.yaml</FONT></TD></TR></TABLE>>,
                likec4_id="h3RoutingPlatform.apiGateway.datasetRegistry",
                likec4_level=2,
                margin="0.223,0.223",
                width=4.445];
            coordtranslator [color="#4f46e5",
                fillcolor="#6366f1",
                fontcolor="#eef2ff",
                group="h3RoutingPlatform.apiGateway",
                height=2.5,
                label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">coordTranslator</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Converts lat/lon to graph edge IDs via<BR/>spatial index</FONT></TD></TR></TABLE>>,
                likec4_id="h3RoutingPlatform.apiGateway.coordTranslator",
                likec4_level=2,
                margin="0.223,0.223",
                width=4.445];
        }
        subgraph cluster_cppengine {
            graph [color="#1b3d88",
                fillcolor="#194b9e",
                label=<<FONT POINT-SIZE="11" COLOR="#bfdbfeb3"><B>C++ ROUTING ENGINE</B></FONT>>,
                likec4_depth=1,
                likec4_id="h3RoutingPlatform.cppEngine",
                likec4_level=1,
                margin=40,
                style=filled
            ];
            queryalgorithms [color="#4f46e5",
                fillcolor="#6366f1",
                fontcolor="#eef2ff",
                group="h3RoutingPlatform.cppEngine",
                height=2.5,
                label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">queryAlgorithms</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Dijkstra, Bidirectional, Pruned,<BR/>Unidirectional CH</FONT></TD></TR></TABLE>>,
                likec4_id="h3RoutingPlatform.cppEngine.queryAlgorithms",
                likec4_level=2,
                margin="0.223,0.223",
                width=4.445];
            spatialindex [color="#4f46e5",
                fillcolor="#6366f1",
                fontcolor="#eef2ff",
                group="h3RoutingPlatform.cppEngine",
                height=2.5,
                label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">spatialIndex</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">H3 or R-tree index for nearest edge lookup</FONT></TD></TR></TABLE>>,
                likec4_id="h3RoutingPlatform.cppEngine.spatialIndex",
                likec4_level=2,
                margin="0.223,0.223",
                width=4.445];
            csrgraph [color="#4f46e5",
                fillcolor="#6366f1",
                fontcolor="#eef2ff",
                group="h3RoutingPlatform.cppEngine",
                height=2.5,
                label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">csrGraph</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Compressed Sparse Row graph for memory<BR/>efficiency</FONT></TD></TR></TABLE>>,
                likec4_id="h3RoutingPlatform.cppEngine.csrGraph",
                likec4_level=2,
                margin="0.223,0.223",
                width=4.445];
            pathexpander [color="#4f46e5",
                fillcolor="#6366f1",
                fontcolor="#eef2ff",
                group="h3RoutingPlatform.cppEngine",
                height=2.5,
                label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">pathExpander</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Resolves shortcut paths to base edge<BR/>sequences</FONT></TD></TR></TABLE>>,
                likec4_id="h3RoutingPlatform.cppEngine.pathExpander",
                likec4_level=2,
                margin="0.223,0.223",
                width=4.445];
            shortcutgraph [color="#4f46e5",
                fillcolor="#6366f1",
                fontcolor="#eef2ff",
                group="h3RoutingPlatform.cppEngine",
                height=2.5,
                label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">shortcutGraph</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#c7d2fe">Graph with adjacency lists, shortcuts, and<BR/>edge metadata</FONT></TD></TR></TABLE>>,
                likec4_id="h3RoutingPlatform.cppEngine.shortcutGraph",
                likec4_level=2,
                margin="0.223,0.223",
                width=4.445];
        }
        streamlitui [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Streamlit UI</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">Python / Streamlit</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Interactive map visualization and debugging<BR/>interface</FONT></TD></TR></TABLE>>,
            likec4_id="h3RoutingPlatform.streamlitUI",
            likec4_level=1,
            margin="0.223,0.223",
            width=4.445];
    }
    developer [color="#7E451D",
        fillcolor="#A35829",
        fontcolor="#FFE0C2",
        height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Developer</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#f9b27c">Uses Streamlit UI for testing and Python SDK<BR/>for integration</FONT></TD></TR></TABLE>>,
        likec4_id=developer,
        likec4_level=0,
        margin="0.223,0.223",
        width=4.445];
    developer -> streamlitui [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Uses for visualization</FONT></TD></TR></TABLE>>,
        likec4_id="1e5blbv",
        minlen=1,
        style=dashed];
    streamlitui -> routehandler [arrowhead=normal,
        lhead=cluster_apigateway,
        likec4_id="1in9qsb",
        style=dashed,
        weight=2,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">HTTP requests</FONT></TD></TR></TABLE>>];
    routehandler -> datasetregistry [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Loads from</FONT></TD></TR></TABLE>>,
        likec4_id="1hnai0c",
        minlen=1,
        style=dashed];
    routehandler -> coordtranslator [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Uses</FONT></TD></TR></TABLE>>,
        likec4_id="4dg36o",
        style=dashed];
    coordtranslator -> queryalgorithms [arrowhead=normal,
        lhead=cluster_cppengine,
        likec4_id=zp2xqf,
        ltail=cluster_apigateway,
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Route queries (port 8082)</FONT></TD></TR></TABLE>>];
    queryalgorithms -> csrgraph [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Queries</FONT></TD></TR></TABLE>>,
        likec4_id=ai2pea,
        minlen=1,
        style=dashed];
    queryalgorithms -> pathexpander [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Expands shortcuts</FONT></TD></TR></TABLE>>,
        likec4_id="1maacps",
        minlen=1,
        style=dashed];
    queryalgorithms -> shortcutgraph [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Queries</FONT></TD></TR></TABLE>>,
        likec4_id=g32vts,
        style=dashed];
    spatialindex -> shortcutgraph [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">Indexes edges</FONT></TD></TR></TABLE>>,
        likec4_id="11z7ybe",
        minlen=1,
        style=dashed];
}
`;default:throw new Error("Unknown viewId: "+e)}}function n(e){switch(e){case"index":return`<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
 "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<!-- Generated by graphviz version 14.0.4 (0)
 -->
<!-- Pages: 1 -->
<svg width="820pt" height="533pt"
 viewBox="0.00 0.00 820.00 533.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(15.05 517.85)">
<!-- developer -->
<g id="node1" class="node">
<title>developer</title>
<polygon fill="#a35829" stroke="#7e451d" stroke-width="0" points="341.91,-502.8 0,-502.8 0,-322.8 341.91,-322.8 341.91,-502.8"/>
<text xml:space="preserve" text-anchor="start" x="125.37" y="-426.8" font-family="Arial" font-size="20.00" fill="#ffe0c2">Developer</text>
<text xml:space="preserve" text-anchor="start" x="20.06" y="-403.3" font-family="Arial" font-size="15.00" fill="#f9b27c">Uses Streamlit UI for testing and Python SDK</text>
<text xml:space="preserve" text-anchor="start" x="125.09" y="-385.3" font-family="Arial" font-size="15.00" fill="#f9b27c">for integration</text>
</g>
<!-- h3routingplatform -->
<g id="node2" class="node">
<title>h3routingplatform</title>
<polygon fill="#0284c7" stroke="#0369a1" stroke-width="0" points="556.91,-180 234.99,-180 234.99,0 556.91,0 556.91,-180"/>
<text xml:space="preserve" text-anchor="start" x="305.91" y="-104" font-family="Arial" font-size="20.00" fill="#f0f9ff">H3 Routing Platform</text>
<text xml:space="preserve" text-anchor="start" x="255.05" y="-80.5" font-family="Arial" font-size="15.00" fill="#b6ecf7">High&#45;performance H3&#45;indexed Contraction</text>
<text xml:space="preserve" text-anchor="start" x="314.24" y="-62.5" font-family="Arial" font-size="15.00" fill="#b6ecf7">Hierarchy routing engine</text>
</g>
<!-- externalclient -->
<g id="node3" class="node">
<title>externalclient</title>
<polygon fill="#a35829" stroke="#7e451d" stroke-width="0" points="789.84,-502.8 452.07,-502.8 452.07,-322.8 789.84,-322.8 789.84,-502.8"/>
<text xml:space="preserve" text-anchor="start" x="555.92" y="-426.8" font-family="Arial" font-size="20.00" fill="#ffe0c2">External Client</text>
<text xml:space="preserve" text-anchor="start" x="472.12" y="-403.3" font-family="Arial" font-size="15.00" fill="#f9b27c">Any application consuming the routing REST</text>
<text xml:space="preserve" text-anchor="start" x="608.86" y="-385.3" font-family="Arial" font-size="15.00" fill="#f9b27c">API</text>
</g>
<!-- developer&#45;&gt;h3routingplatform -->
<g id="edge1" class="edge">
<title>developer&#45;&gt;h3routingplatform</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M233.33,-322.87C262.65,-281.06 297.69,-231.11 327.71,-188.29"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="329.75,-189.96 331.91,-182.31 325.46,-186.94 329.75,-189.96"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="290.2,-240 290.2,-262.8 317.19,-262.8 317.19,-240 290.2,-240"/>
<text xml:space="preserve" text-anchor="start" x="293.2" y="-248.2" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">[...]</text>
</g>
<!-- externalclient&#45;&gt;h3routingplatform -->
<g id="edge2" class="edge">
<title>externalclient&#45;&gt;h3routingplatform</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M558.58,-322.87C529.25,-281.06 494.22,-231.11 464.19,-188.29"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="466.45,-186.94 459.99,-182.31 462.15,-189.96 466.45,-186.94"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="515.2,-240 515.2,-262.8 616.89,-262.8 616.89,-240 515.2,-240"/>
<text xml:space="preserve" text-anchor="start" x="518.2" y="-247.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">REST API calls</text>
</g>
</g>
</svg>
`;case"containerView":return`<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
 "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<!-- Generated by graphviz version 14.0.4 (0)
 -->
<!-- Pages: 1 -->
<svg width="2124pt" height="1558pt"
 viewBox="0.00 0.00 2124.00 1558.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(15.05 1543.45)">
<g id="clust1" class="cluster">
<title>cluster_h3routingplatform</title>
<polygon fill="#0d4b6c" stroke="#0b3c57" points="377.89,-8 377.89,-1257.6 2085.89,-1257.6 2085.89,-8 377.89,-8"/>
<text xml:space="preserve" text-anchor="start" x="385.89" y="-1244.7" font-family="Arial" font-weight="bold" font-size="11.00" fill="#b6ecf7" fill-opacity="0.701961">H3 ROUTING PLATFORM</text>
</g>
<!-- streamlitui -->
<g id="node1" class="node">
<title>streamlitui</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="749.87,-1196.4 417.9,-1196.4 417.9,-1016.4 749.87,-1016.4 749.87,-1196.4"/>
<text xml:space="preserve" text-anchor="start" x="531.66" y="-1130.2" font-family="Arial" font-size="20.00" fill="#eff6ff">Streamlit UI</text>
<text xml:space="preserve" text-anchor="start" x="532.59" y="-1108.5" font-family="Arial" font-size="13.00" fill="#bfdbfe">Python / Streamlit</text>
<text xml:space="preserve" text-anchor="start" x="437.96" y="-1087.1" font-family="Arial" font-size="15.00" fill="#bfdbfe">Interactive map visualization and debugging</text>
<text xml:space="preserve" text-anchor="start" x="555.12" y="-1069.1" font-family="Arial" font-size="15.00" fill="#bfdbfe">interface</text>
</g>
<!-- pythonsdk -->
<g id="node2" class="node">
<title>pythonsdk</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1185.93,-1196.4 859.85,-1196.4 859.85,-1016.4 1185.93,-1016.4 1185.93,-1196.4"/>
<text xml:space="preserve" text-anchor="start" x="968.42" y="-1130.2" font-family="Arial" font-size="20.00" fill="#eff6ff">Python SDK</text>
<text xml:space="preserve" text-anchor="start" x="1002.65" y="-1108.5" font-family="Arial" font-size="13.00" fill="#bfdbfe">Python</text>
<text xml:space="preserve" text-anchor="start" x="879.9" y="-1087.1" font-family="Arial" font-size="15.00" fill="#bfdbfe">h3&#45;routing&#45;client package for programmatic</text>
<text xml:space="preserve" text-anchor="start" x="999.55" y="-1069.1" font-family="Arial" font-size="15.00" fill="#bfdbfe">access</text>
</g>
<!-- osmdata -->
<g id="node3" class="node">
<title>osmdata</title>
<path fill="#64748b" stroke="#475569" stroke-width="2" d="M1615.91,-1180.04C1615.91,-1189.07 1544.18,-1196.4 1455.89,-1196.4 1367.59,-1196.4 1295.87,-1189.07 1295.87,-1180.04 1295.87,-1180.04 1295.87,-1032.76 1295.87,-1032.76 1295.87,-1023.73 1367.59,-1016.4 1455.89,-1016.4 1544.18,-1016.4 1615.91,-1023.73 1615.91,-1032.76 1615.91,-1032.76 1615.91,-1180.04 1615.91,-1180.04"/>
<path fill="none" stroke="#475569" stroke-width="2" d="M1615.91,-1180.04C1615.91,-1171.01 1544.18,-1163.67 1455.89,-1163.67 1367.59,-1163.67 1295.87,-1171.01 1295.87,-1180.04"/>
<text xml:space="preserve" text-anchor="start" x="1363.07" y="-1111.4" font-family="Arial" font-size="20.00" fill="#f8fafc">OpenStreetMap PBF</text>
<text xml:space="preserve" text-anchor="start" x="1382.93" y="-1087.9" font-family="Arial" font-size="15.00" fill="#cbd5e1">Raw map data source</text>
</g>
<!-- h3toolkit -->
<g id="node4" class="node">
<title>h3toolkit</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="2045.91,-1196.4 1725.87,-1196.4 1725.87,-1016.4 2045.91,-1016.4 2045.91,-1196.4"/>
<text xml:space="preserve" text-anchor="start" x="1840.87" y="-1121.2" font-family="Arial" font-size="20.00" fill="#eff6ff">H3 Toolkit</text>
<text xml:space="preserve" text-anchor="start" x="1847.95" y="-1099.5" font-family="Arial" font-size="13.00" fill="#bfdbfe">C++ / Python</text>
<text xml:space="preserve" text-anchor="start" x="1778.76" y="-1078.1" font-family="Arial" font-size="15.00" fill="#bfdbfe">Shared H3 spatial utilities library</text>
</g>
<!-- apigateway -->
<g id="node5" class="node">
<title>apigateway</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="852.95,-550.8 516.83,-550.8 516.83,-370.8 852.95,-370.8 852.95,-550.8"/>
<text xml:space="preserve" text-anchor="start" x="626.53" y="-484.6" font-family="Arial" font-size="20.00" fill="#eff6ff">API Gateway</text>
<text xml:space="preserve" text-anchor="start" x="636.12" y="-462.9" font-family="Arial" font-size="13.00" fill="#bfdbfe">Python / FastAPI</text>
<text xml:space="preserve" text-anchor="start" x="536.88" y="-441.5" font-family="Arial" font-size="15.00" fill="#bfdbfe">REST API on port 8000, coordinates dataset</text>
<text xml:space="preserve" text-anchor="start" x="582.32" y="-423.5" font-family="Arial" font-size="15.00" fill="#bfdbfe">loading and request translation</text>
</g>
<!-- duckosm -->
<g id="node6" class="node">
<title>duckosm</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1618.51,-873.6 1293.27,-873.6 1293.27,-693.6 1618.51,-693.6 1618.51,-873.6"/>
<text xml:space="preserve" text-anchor="start" x="1411.99" y="-807.4" font-family="Arial" font-size="20.00" fill="#eff6ff">duckOSM</text>
<text xml:space="preserve" text-anchor="start" x="1406.4" y="-785.7" font-family="Arial" font-size="13.00" fill="#bfdbfe">Python / DuckDB</text>
<text xml:space="preserve" text-anchor="start" x="1313.32" y="-764.3" font-family="Arial" font-size="15.00" fill="#bfdbfe">Converts OpenStreetMap PBF files to road</text>
<text xml:space="preserve" text-anchor="start" x="1392.12" y="-746.3" font-family="Arial" font-size="15.00" fill="#bfdbfe">network in DuckDB</text>
</g>
<!-- shortcutgenerator -->
<g id="node7" class="node">
<title>shortcutgenerator</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1809.91,-228 1489.87,-228 1489.87,-48 1809.91,-48 1809.91,-228"/>
<text xml:space="preserve" text-anchor="start" x="1564.84" y="-161.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Shortcut Generator</text>
<text xml:space="preserve" text-anchor="start" x="1600.4" y="-140.1" font-family="Arial" font-size="13.00" fill="#bfdbfe">Python / DuckDB</text>
<text xml:space="preserve" text-anchor="start" x="1532.33" y="-118.7" font-family="Arial" font-size="15.00" fill="#bfdbfe">4&#45;phase H3 hierarchy processor for</text>
<text xml:space="preserve" text-anchor="start" x="1580.69" y="-100.7" font-family="Arial" font-size="15.00" fill="#bfdbfe">contraction shortcuts</text>
</g>
<!-- duckdb -->
<g id="node8" class="node">
<title>duckdb</title>
<path fill="#64748b" stroke="#475569" stroke-width="2" d="M1622.7,-534.44C1622.7,-543.47 1547.93,-550.8 1455.89,-550.8 1363.84,-550.8 1289.07,-543.47 1289.07,-534.44 1289.07,-534.44 1289.07,-387.16 1289.07,-387.16 1289.07,-378.13 1363.84,-370.8 1455.89,-370.8 1547.93,-370.8 1622.7,-378.13 1622.7,-387.16 1622.7,-387.16 1622.7,-534.44 1622.7,-534.44"/>
<path fill="none" stroke="#475569" stroke-width="2" d="M1622.7,-534.44C1622.7,-525.41 1547.93,-518.07 1455.89,-518.07 1363.84,-518.07 1289.07,-525.41 1289.07,-534.44"/>
<text xml:space="preserve" text-anchor="start" x="1373.63" y="-474.8" font-family="Arial" font-size="20.00" fill="#f8fafc">DuckDB Database</text>
<text xml:space="preserve" text-anchor="start" x="1309.13" y="-451.3" font-family="Arial" font-size="15.00" fill="#cbd5e1">Stores edges, nodes, shortcuts, and dataset</text>
<text xml:space="preserve" text-anchor="start" x="1443.8" y="-433.3" font-family="Arial" font-size="15.00" fill="#cbd5e1">info</text>
</g>
<!-- cppengine -->
<g id="node9" class="node">
<title>cppengine</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="862.11,-228 507.66,-228 507.66,-48 862.11,-48 862.11,-228"/>
<text xml:space="preserve" text-anchor="start" x="594.82" y="-161.8" font-family="Arial" font-size="20.00" fill="#eff6ff">C++ Routing Engine</text>
<text xml:space="preserve" text-anchor="start" x="633.24" y="-140.1" font-family="Arial" font-size="13.00" fill="#bfdbfe">C++ / Crow HTTP</text>
<text xml:space="preserve" text-anchor="start" x="527.72" y="-118.7" font-family="Arial" font-size="15.00" fill="#bfdbfe">High&#45;performance engine on port 8082 with CH</text>
<text xml:space="preserve" text-anchor="start" x="650.29" y="-100.7" font-family="Arial" font-size="15.00" fill="#bfdbfe">algorithms</text>
</g>
<!-- developer -->
<g id="node10" class="node">
<title>developer</title>
<polygon fill="#a35829" stroke="#7e451d" stroke-width="0" points="973.84,-1528.4 631.93,-1528.4 631.93,-1348.4 973.84,-1348.4 973.84,-1528.4"/>
<text xml:space="preserve" text-anchor="start" x="757.31" y="-1452.4" font-family="Arial" font-size="20.00" fill="#ffe0c2">Developer</text>
<text xml:space="preserve" text-anchor="start" x="651.99" y="-1428.9" font-family="Arial" font-size="15.00" fill="#f9b27c">Uses Streamlit UI for testing and Python SDK</text>
<text xml:space="preserve" text-anchor="start" x="757.03" y="-1410.9" font-family="Arial" font-size="15.00" fill="#f9b27c">for integration</text>
</g>
<!-- externalclient -->
<g id="node11" class="node">
<title>externalclient</title>
<polygon fill="#a35829" stroke="#7e451d" stroke-width="0" points="337.78,-873.6 0,-873.6 0,-693.6 337.78,-693.6 337.78,-873.6"/>
<text xml:space="preserve" text-anchor="start" x="103.86" y="-797.6" font-family="Arial" font-size="20.00" fill="#ffe0c2">External Client</text>
<text xml:space="preserve" text-anchor="start" x="20.06" y="-774.1" font-family="Arial" font-size="15.00" fill="#f9b27c">Any application consuming the routing REST</text>
<text xml:space="preserve" text-anchor="start" x="156.8" y="-756.1" font-family="Arial" font-size="15.00" fill="#f9b27c">API</text>
</g>
<!-- streamlitui&#45;&gt;apigateway -->
<g id="edge4" class="edge">
<title>streamlitui&#45;&gt;apigateway</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M597.83,-1016.59C616.56,-897.18 649.78,-685.53 669.32,-561.03"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="671.89,-561.54 670.46,-553.73 666.71,-560.73 671.89,-561.54"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="647.71,-772.2 647.71,-795 747.85,-795 747.85,-772.2 647.71,-772.2"/>
<text xml:space="preserve" text-anchor="start" x="650.71" y="-779.4" font-family="Arial" font-size="14.00" fill="#c9c9c9">HTTP requests</text>
</g>
<!-- pythonsdk&#45;&gt;apigateway -->
<g id="edge5" class="edge">
<title>pythonsdk&#45;&gt;apigateway</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M976.25,-1016.59C913.35,-896.82 801.72,-684.26 736.41,-559.9"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="738.81,-558.83 733,-553.42 734.16,-561.28 738.81,-558.83"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="898.48,-772.2 898.48,-795 998.62,-795 998.62,-772.2 898.48,-772.2"/>
<text xml:space="preserve" text-anchor="start" x="901.48" y="-779.4" font-family="Arial" font-size="14.00" fill="#c9c9c9">HTTP requests</text>
</g>
<!-- osmdata&#45;&gt;duckosm -->
<g id="edge6" class="edge">
<title>osmdata&#45;&gt;duckosm</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1455.89,-1015.61C1455.89,-974.6 1455.89,-925.89 1455.89,-883.8"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1458.51,-884.06 1455.89,-876.56 1453.26,-884.06 1458.51,-884.06"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1455.89,-933.6 1455.89,-956.4 1493.03,-956.4 1493.03,-933.6 1455.89,-933.6"/>
<text xml:space="preserve" text-anchor="start" x="1458.89" y="-940.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">Input</text>
</g>
<!-- h3toolkit&#45;&gt;shortcutgenerator -->
<g id="edge7" class="edge">
<title>h3toolkit&#45;&gt;shortcutgenerator</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1866.07,-1016.5C1832.24,-866.04 1760.35,-551.82 1691.89,-288 1687.66,-271.69 1682.98,-254.43 1678.33,-237.67"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1680.95,-237.3 1676.41,-230.78 1675.89,-238.71 1680.95,-237.3"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1777.18,-610.8 1777.18,-633.6 1847.76,-633.6 1847.76,-610.8 1777.18,-610.8"/>
<text xml:space="preserve" text-anchor="start" x="1780.18" y="-618" font-family="Arial" font-size="14.00" fill="#c9c9c9">H3 utilities</text>
</g>
<!-- apigateway&#45;&gt;cppengine -->
<g id="edge8" class="edge">
<title>apigateway&#45;&gt;cppengine</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M684.89,-370.87C684.89,-329.67 684.89,-280.56 684.89,-238.17"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="687.51,-238.36 684.89,-230.86 682.26,-238.36 687.51,-238.36"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="684.89,-288 684.89,-310.8 850.42,-310.8 850.42,-288 684.89,-288"/>
<text xml:space="preserve" text-anchor="start" x="687.89" y="-295.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">Route queries (port 8082)</text>
</g>
<!-- duckosm&#45;&gt;duckdb -->
<g id="edge9" class="edge">
<title>duckosm&#45;&gt;duckdb</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1455.89,-693.67C1455.89,-652.81 1455.89,-604.18 1455.89,-562.03"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1458.51,-562.27 1455.89,-554.77 1453.26,-562.27 1458.51,-562.27"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1455.89,-610.8 1455.89,-633.6 1582.51,-633.6 1582.51,-610.8 1455.89,-610.8"/>
<text xml:space="preserve" text-anchor="start" x="1458.89" y="-618" font-family="Arial" font-size="14.00" fill="#c9c9c9">Creates road graph</text>
</g>
<!-- shortcutgenerator&#45;&gt;duckdb -->
<g id="edge10" class="edge">
<title>shortcutgenerator&#45;&gt;duckdb</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1596.11,-227.93C1571.11,-269.27 1541.3,-318.57 1515.6,-361.05"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1513.39,-359.65 1511.75,-367.42 1517.88,-362.36 1513.39,-359.65"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1558.7,-288 1558.7,-310.8 1665.06,-310.8 1665.06,-288 1558.7,-288"/>
<text xml:space="preserve" text-anchor="start" x="1561.7" y="-295.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">Writes shortcuts</text>
</g>
<!-- duckdb&#45;&gt;shortcutgenerator -->
<g id="edge11" class="edge">
<title>duckdb&#45;&gt;shortcutgenerator</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1429.8,-370.09C1426.46,-342.51 1427.89,-312.89 1440.72,-288 1451.22,-267.63 1465.93,-249.43 1482.75,-233.35"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1484.12,-235.66 1487.86,-228.64 1480.56,-231.8 1484.12,-235.66"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1440.72,-288 1440.72,-310.8 1519.89,-310.8 1519.89,-288 1440.72,-288"/>
<text xml:space="preserve" text-anchor="start" x="1443.72" y="-295.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">Input edges</text>
</g>
<!-- duckdb&#45;&gt;cppengine -->
<g id="edge12" class="edge">
<title>duckdb&#45;&gt;cppengine</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1288.12,-389.99C1165.27,-338.88 998.54,-269.5 871.5,-216.64"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="872.76,-214.33 864.83,-213.87 870.74,-219.18 872.76,-214.33"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1093.51,-288 1093.51,-310.8 1199.9,-310.8 1199.9,-288 1093.51,-288"/>
<text xml:space="preserve" text-anchor="start" x="1096.51" y="-295.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">Loads at startup</text>
</g>
<!-- developer&#45;&gt;streamlitui -->
<g id="edge1" class="edge">
<title>developer&#45;&gt;streamlitui</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M741.35,-1348.65C727.83,-1328.89 713.65,-1307.99 700.61,-1288.4 682.67,-1261.43 663.5,-1231.99 646,-1204.84"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="648.28,-1203.54 642.01,-1198.66 643.87,-1206.38 648.28,-1203.54"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="700.61,-1265.6 700.61,-1288.4 838.89,-1288.4 838.89,-1265.6 700.61,-1265.6"/>
<text xml:space="preserve" text-anchor="start" x="703.61" y="-1272.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">Uses for visualization</text>
</g>
<!-- developer&#45;&gt;pythonsdk -->
<g id="edge2" class="edge">
<title>developer&#45;&gt;pythonsdk</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M862.13,-1348.53C891.72,-1304.14 927.59,-1250.34 957.93,-1204.83"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="960.07,-1206.36 962.05,-1198.66 955.7,-1203.44 960.07,-1206.36"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="912.89,-1265.6 912.89,-1288.4 1002.94,-1288.4 1002.94,-1265.6 912.89,-1265.6"/>
<text xml:space="preserve" text-anchor="start" x="915.89" y="-1272.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">Integrates via</text>
</g>
<!-- externalclient&#45;&gt;apigateway -->
<g id="edge3" class="edge">
<title>externalclient&#45;&gt;apigateway</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M311.94,-693.67C380.73,-650.9 463.22,-599.61 533.11,-556.16"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="534.45,-558.42 539.44,-552.23 531.68,-553.96 534.45,-558.42"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="442.36,-610.8 442.36,-633.6 544.05,-633.6 544.05,-610.8 442.36,-610.8"/>
<text xml:space="preserve" text-anchor="start" x="445.36" y="-618" font-family="Arial" font-size="14.00" fill="#c9c9c9">REST API calls</text>
</g>
</g>
</svg>
`;case"dataPipeline":return`<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
 "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<!-- Generated by graphviz version 14.0.4 (0)
 -->
<!-- Pages: 1 -->
<svg width="1309pt" height="2457pt"
 viewBox="0.00 0.00 1309.00 2457.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(15.05 2442.05)">
<g id="clust1" class="cluster">
<title>cluster_shortcutgenerator</title>
<polygon fill="#194b9e" stroke="#1b3d88" points="390.02,-282.8 390.02,-2178 1271.02,-2178 1271.02,-282.8 390.02,-282.8"/>
<text xml:space="preserve" text-anchor="start" x="398.02" y="-2165.1" font-family="Arial" font-weight="bold" font-size="11.00" fill="#bfdbfe" fill-opacity="0.701961">SHORTCUT GENERATOR</text>
</g>
<!-- dataloader -->
<g id="node1" class="node">
<title>dataloader</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="886.6,-2116.8 525.44,-2116.8 525.44,-1936.8 886.6,-1936.8 886.6,-2116.8"/>
<text xml:space="preserve" text-anchor="start" x="655.42" y="-2040.8" font-family="Arial" font-size="20.00" fill="#eef2ff">dataLoader</text>
<text xml:space="preserve" text-anchor="start" x="545.5" y="-2017.3" font-family="Arial" font-size="15.00" fill="#c7d2fe">Loads edges and edge_graph from DuckDB into</text>
<text xml:space="preserve" text-anchor="start" x="658.08" y="-1999.3" font-family="Arial" font-size="15.00" fill="#c7d2fe">working tables</text>
</g>
<!-- phase1 -->
<g id="node2" class="node">
<title>phase1</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="867.4,-1794 544.64,-1794 544.64,-1614 867.4,-1614 867.4,-1794"/>
<text xml:space="preserve" text-anchor="start" x="584.29" y="-1718" font-family="Arial" font-size="20.00" fill="#eef2ff">Phase 1: Forward Chunked</text>
<text xml:space="preserve" text-anchor="start" x="564.7" y="-1694.5" font-family="Arial" font-size="15.00" fill="#c7d2fe">Processes res 15→7 in parallel chunks per</text>
<text xml:space="preserve" text-anchor="start" x="666" y="-1676.5" font-family="Arial" font-size="15.00" fill="#c7d2fe">partition cell</text>
</g>
<!-- cellassigner -->
<g id="node3" class="node">
<title>cellassigner</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="775.56,-1471.2 444.48,-1471.2 444.48,-1291.2 775.56,-1291.2 775.56,-1471.2"/>
<text xml:space="preserve" text-anchor="start" x="556.11" y="-1395.2" font-family="Arial" font-size="20.00" fill="#eef2ff">cellAssigner</text>
<text xml:space="preserve" text-anchor="start" x="464.53" y="-1371.7" font-family="Arial" font-size="15.00" fill="#c7d2fe">Assigns shortcuts to H3 cells based on LCA</text>
<text xml:space="preserve" text-anchor="start" x="577.5" y="-1353.7" font-family="Arial" font-size="15.00" fill="#c7d2fe">resolution</text>
</g>
<!-- phase2 -->
<g id="node4" class="node">
<title>phase2</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="1224.4,-1471.2 891.64,-1471.2 891.64,-1291.2 1224.4,-1291.2 1224.4,-1471.2"/>
<text xml:space="preserve" text-anchor="start" x="915.72" y="-1395.2" font-family="Arial" font-size="20.00" fill="#eef2ff">Phase 2: Forward Consolidation</text>
<text xml:space="preserve" text-anchor="start" x="911.69" y="-1371.7" font-family="Arial" font-size="15.00" fill="#c7d2fe">Merges cells upward res 6→0, deduplicating</text>
<text xml:space="preserve" text-anchor="start" x="1032.59" y="-1353.7" font-family="Arial" font-size="15.00" fill="#c7d2fe">via cost</text>
</g>
<!-- shortestpathsolver -->
<g id="node5" class="node">
<title>shortestpathsolver</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="781.55,-1148.4 430.49,-1148.4 430.49,-968.4 781.55,-968.4 781.55,-1148.4"/>
<text xml:space="preserve" text-anchor="start" x="521.53" y="-1072.4" font-family="Arial" font-size="20.00" fill="#eef2ff">shortestPathSolver</text>
<text xml:space="preserve" text-anchor="start" x="450.55" y="-1048.9" font-family="Arial" font-size="15.00" fill="#c7d2fe">Computes optimal shortcuts via SciPy/DuckDB</text>
<text xml:space="preserve" text-anchor="start" x="550.16" y="-1030.9" font-family="Arial" font-size="15.00" fill="#c7d2fe">graph algorithms</text>
</g>
<!-- phase3 -->
<g id="node6" class="node">
<title>phase3</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="1230.61,-1148.4 891.43,-1148.4 891.43,-968.4 1230.61,-968.4 1230.61,-1148.4"/>
<text xml:space="preserve" text-anchor="start" x="911.49" y="-1072.4" font-family="Arial" font-size="20.00" fill="#eef2ff">Phase 3: Backward Consolidation</text>
<text xml:space="preserve" text-anchor="start" x="958.06" y="-1048.9" font-family="Arial" font-size="15.00" fill="#c7d2fe">Splits cells downward res 0→7,</text>
<text xml:space="preserve" text-anchor="start" x="982.65" y="-1030.9" font-family="Arial" font-size="15.00" fill="#c7d2fe">re&#45;partitioning shortcuts</text>
</g>
<!-- deduplicator -->
<g id="node7" class="node">
<title>deduplicator</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="791.99,-825.6 430.05,-825.6 430.05,-645.6 791.99,-645.6 791.99,-825.6"/>
<text xml:space="preserve" text-anchor="start" x="556.54" y="-749.6" font-family="Arial" font-size="20.00" fill="#eef2ff">deduplicator</text>
<text xml:space="preserve" text-anchor="start" x="450.11" y="-726.1" font-family="Arial" font-size="15.00" fill="#c7d2fe">Removes redundant shortcuts keeping minimum</text>
<text xml:space="preserve" text-anchor="start" x="597.27" y="-708.1" font-family="Arial" font-size="15.00" fill="#c7d2fe">cost</text>
</g>
<!-- phase4 -->
<g id="node8" class="node">
<title>phase4</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="1222.04,-825.6 902,-825.6 902,-645.6 1222.04,-645.6 1222.04,-825.6"/>
<text xml:space="preserve" text-anchor="start" x="933.06" y="-749.6" font-family="Arial" font-size="20.00" fill="#eef2ff">Phase 4: Backward Chunked</text>
<text xml:space="preserve" text-anchor="start" x="931.54" y="-726.1" font-family="Arial" font-size="15.00" fill="#c7d2fe">Processes res 8→15 in parallel chunks,</text>
<text xml:space="preserve" text-anchor="start" x="984.9" y="-708.1" font-family="Arial" font-size="15.00" fill="#c7d2fe">finalizing all resolutions</text>
</g>
<!-- finalizer -->
<g id="node9" class="node">
<title>finalizer</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="1230.73,-502.8 881.31,-502.8 881.31,-322.8 1230.73,-322.8 1230.73,-502.8"/>
<text xml:space="preserve" text-anchor="start" x="1021.56" y="-426.8" font-family="Arial" font-size="20.00" fill="#eef2ff">finalizer</text>
<text xml:space="preserve" text-anchor="start" x="901.36" y="-403.3" font-family="Arial" font-size="15.00" fill="#c7d2fe">Exports final shortcuts to Parquet and DuckDB</text>
<text xml:space="preserve" text-anchor="start" x="1029.76" y="-385.3" font-family="Arial" font-size="15.00" fill="#c7d2fe">schema</text>
</g>
<!-- osmdata -->
<g id="node10" class="node">
<title>osmdata</title>
<path fill="#64748b" stroke="#475569" stroke-width="2" d="M320.04,-809.24C320.04,-818.27 248.32,-825.6 160.02,-825.6 71.72,-825.6 0,-818.27 0,-809.24 0,-809.24 0,-661.96 0,-661.96 0,-652.93 71.72,-645.6 160.02,-645.6 248.32,-645.6 320.04,-652.93 320.04,-661.96 320.04,-661.96 320.04,-809.24 320.04,-809.24"/>
<path fill="none" stroke="#475569" stroke-width="2" d="M320.04,-809.24C320.04,-800.21 248.32,-792.87 160.02,-792.87 71.72,-792.87 0,-800.21 0,-809.24"/>
<text xml:space="preserve" text-anchor="start" x="67.2" y="-740.6" font-family="Arial" font-size="20.00" fill="#f8fafc">OpenStreetMap PBF</text>
<text xml:space="preserve" text-anchor="start" x="87.07" y="-717.1" font-family="Arial" font-size="15.00" fill="#cbd5e1">Raw map data source</text>
</g>
<!-- duckosm -->
<g id="node11" class="node">
<title>duckosm</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="336.64,-502.8 11.4,-502.8 11.4,-322.8 336.64,-322.8 336.64,-502.8"/>
<text xml:space="preserve" text-anchor="start" x="130.12" y="-436.6" font-family="Arial" font-size="20.00" fill="#eff6ff">duckOSM</text>
<text xml:space="preserve" text-anchor="start" x="124.53" y="-414.9" font-family="Arial" font-size="13.00" fill="#bfdbfe">Python / DuckDB</text>
<text xml:space="preserve" text-anchor="start" x="31.45" y="-393.5" font-family="Arial" font-size="15.00" fill="#bfdbfe">Converts OpenStreetMap PBF files to road</text>
<text xml:space="preserve" text-anchor="start" x="110.25" y="-375.5" font-family="Arial" font-size="15.00" fill="#bfdbfe">network in DuckDB</text>
</g>
<!-- h3toolkit -->
<g id="node12" class="node">
<title>h3toolkit</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="866.04,-2427 546,-2427 546,-2247 866.04,-2247 866.04,-2427"/>
<text xml:space="preserve" text-anchor="start" x="661.01" y="-2351.8" font-family="Arial" font-size="20.00" fill="#eff6ff">H3 Toolkit</text>
<text xml:space="preserve" text-anchor="start" x="668.08" y="-2330.1" font-family="Arial" font-size="13.00" fill="#bfdbfe">C++ / Python</text>
<text xml:space="preserve" text-anchor="start" x="598.89" y="-2308.7" font-family="Arial" font-size="15.00" fill="#bfdbfe">Shared H3 spatial utilities library</text>
</g>
<!-- duckdb -->
<g id="node13" class="node">
<title>duckdb</title>
<path fill="#64748b" stroke="#475569" stroke-width="2" d="M340.84,-163.64C340.84,-172.67 266.07,-180 174.02,-180 81.97,-180 7.2,-172.67 7.2,-163.64 7.2,-163.64 7.2,-16.36 7.2,-16.36 7.2,-7.33 81.97,0 174.02,0 266.07,0 340.84,-7.33 340.84,-16.36 340.84,-16.36 340.84,-163.64 340.84,-163.64"/>
<path fill="none" stroke="#475569" stroke-width="2" d="M340.84,-163.64C340.84,-154.61 266.07,-147.27 174.02,-147.27 81.97,-147.27 7.2,-154.61 7.2,-163.64"/>
<text xml:space="preserve" text-anchor="start" x="91.76" y="-104" font-family="Arial" font-size="20.00" fill="#f8fafc">DuckDB Database</text>
<text xml:space="preserve" text-anchor="start" x="27.26" y="-80.5" font-family="Arial" font-size="15.00" fill="#cbd5e1">Stores edges, nodes, shortcuts, and dataset</text>
<text xml:space="preserve" text-anchor="start" x="161.93" y="-62.5" font-family="Arial" font-size="15.00" fill="#cbd5e1">info</text>
</g>
<!-- dataloader&#45;&gt;phase1 -->
<g id="edge4" class="edge">
<title>dataloader&#45;&gt;phase1</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M706.02,-1936.87C706.02,-1895.67 706.02,-1846.56 706.02,-1804.17"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="708.65,-1804.36 706.02,-1796.86 703.4,-1804.36 708.65,-1804.36"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="706.02,-1854 706.02,-1876.8 792.2,-1876.8 792.2,-1854 706.02,-1854"/>
<text xml:space="preserve" text-anchor="start" x="709.02" y="-1861.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">Loads edges</text>
</g>
<!-- phase1&#45;&gt;cellassigner -->
<g id="edge5" class="edge">
<title>phase1&#45;&gt;cellassigner</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M679.41,-1614.07C667.05,-1572.78 652.32,-1523.55 639.62,-1481.1"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="642.14,-1480.36 637.47,-1473.93 637.11,-1481.87 642.14,-1480.36"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="660.9,-1531.2 660.9,-1554 742.38,-1554 742.38,-1531.2 660.9,-1531.2"/>
<text xml:space="preserve" text-anchor="start" x="663.9" y="-1538.4" font-family="Arial" font-size="14.00" fill="#c9c9c9">Per iteration</text>
</g>
<!-- phase1&#45;&gt;phase2 -->
<g id="edge6" class="edge">
<title>phase1&#45;&gt;phase2</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M803.6,-1614.07C850.05,-1571.73 905.66,-1521.06 953.02,-1477.89"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="954.54,-1480.06 958.31,-1473.07 951,-1476.18 954.54,-1480.06"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="892.57,-1531.2 892.57,-1554 1004.43,-1554 1004.43,-1531.2 892.57,-1531.2"/>
<text xml:space="preserve" text-anchor="start" x="895.57" y="-1538.4" font-family="Arial" font-size="14.00" fill="#c9c9c9">Chunked outputs</text>
</g>
<!-- cellassigner&#45;&gt;shortestpathsolver -->
<g id="edge7" class="edge">
<title>cellassigner&#45;&gt;shortestpathsolver</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M608.91,-1291.27C608.4,-1250.07 607.79,-1200.96 607.26,-1158.57"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="609.88,-1158.72 607.17,-1151.26 604.63,-1158.79 609.88,-1158.72"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="608.14,-1208.4 608.14,-1231.2 712.95,-1231.2 712.95,-1208.4 608.14,-1208.4"/>
<text xml:space="preserve" text-anchor="start" x="611.14" y="-1215.6" font-family="Arial" font-size="14.00" fill="#c9c9c9">Active shortcuts</text>
</g>
<!-- phase2&#45;&gt;phase3 -->
<g id="edge8" class="edge">
<title>phase2&#45;&gt;phase3</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1058.85,-1291.27C1059.24,-1250.07 1059.7,-1200.96 1060.09,-1158.57"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1062.72,-1158.78 1060.16,-1151.26 1057.47,-1158.73 1062.72,-1158.78"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1059.61,-1208.4 1059.61,-1231.2 1197.91,-1231.2 1197.91,-1208.4 1059.61,-1208.4"/>
<text xml:space="preserve" text-anchor="start" x="1062.61" y="-1215.6" font-family="Arial" font-size="14.00" fill="#c9c9c9">Consolidated to res 0</text>
</g>
<!-- shortestpathsolver&#45;&gt;deduplicator -->
<g id="edge9" class="edge">
<title>shortestpathsolver&#45;&gt;deduplicator</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M607.41,-968.47C608.05,-927.27 608.81,-878.16 609.47,-835.77"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="612.1,-836 609.59,-828.46 606.85,-835.91 612.1,-836"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="608.67,-885.6 608.67,-908.4 701.04,-908.4 701.04,-885.6 608.67,-885.6"/>
<text xml:space="preserve" text-anchor="start" x="611.67" y="-892.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">Optimal paths</text>
</g>
<!-- phase3&#45;&gt;phase4 -->
<g id="edge10" class="edge">
<title>phase3&#45;&gt;phase4</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1061.3,-968.47C1061.43,-927.27 1061.58,-878.16 1061.71,-835.77"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1064.34,-835.96 1061.73,-828.46 1059.09,-835.95 1064.34,-835.96"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1061.55,-885.6 1061.55,-908.4 1155.49,-908.4 1155.49,-885.6 1061.55,-885.6"/>
<text xml:space="preserve" text-anchor="start" x="1064.55" y="-892.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">Re&#45;partitioned</text>
</g>
<!-- phase4&#45;&gt;finalizer -->
<g id="edge11" class="edge">
<title>phase4&#45;&gt;finalizer</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1060.36,-645.67C1059.59,-604.47 1058.67,-555.36 1057.87,-512.97"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1060.5,-513.11 1057.74,-505.66 1055.25,-513.2 1060.5,-513.11"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1059.2,-562.8 1059.2,-585.6 1187.39,-585.6 1187.39,-562.8 1059.2,-562.8"/>
<text xml:space="preserve" text-anchor="start" x="1062.2" y="-570" font-family="Arial" font-size="14.00" fill="#c9c9c9">All resolutions done</text>
</g>
<!-- finalizer&#45;&gt;duckdb -->
<g id="edge12" class="edge">
<title>finalizer&#45;&gt;duckdb</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M881.5,-348.32C728.05,-292.51 505.73,-211.65 351.43,-155.53"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="352.62,-153.17 344.67,-153.07 350.82,-158.1 352.62,-153.17"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="641.47,-240 641.47,-262.8 800.73,-262.8 800.73,-240 641.47,-240"/>
<text xml:space="preserve" text-anchor="start" x="644.47" y="-247.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">Writes shortcuts schema</text>
</g>
<!-- osmdata&#45;&gt;duckosm -->
<g id="edge1" class="edge">
<title>osmdata&#45;&gt;duckosm</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M163.94,-644.81C165.73,-603.8 167.85,-555.09 169.69,-513"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="172.3,-513.36 170.01,-505.76 167.06,-513.14 172.3,-513.36"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="167.44,-562.8 167.44,-585.6 204.58,-585.6 204.58,-562.8 167.44,-562.8"/>
<text xml:space="preserve" text-anchor="start" x="170.44" y="-570" font-family="Arial" font-size="14.00" fill="#c9c9c9">Input</text>
</g>
<!-- duckosm&#45;&gt;duckdb -->
<g id="edge3" class="edge">
<title>duckosm&#45;&gt;duckdb</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M174.02,-322.87C174.02,-282.01 174.02,-233.38 174.02,-191.23"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="176.65,-191.47 174.02,-183.97 171.4,-191.47 176.65,-191.47"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="174.02,-240 174.02,-262.8 300.65,-262.8 300.65,-240 174.02,-240"/>
<text xml:space="preserve" text-anchor="start" x="177.02" y="-247.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">Creates road graph</text>
</g>
<!-- h3toolkit&#45;&gt;dataloader -->
<g id="edge2" class="edge">
<title>h3toolkit&#45;&gt;dataloader</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M706.02,-2247.27C706.02,-2228.69 706.02,-2208.56 706.02,-2188.28"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="708.65,-2188.53 706.02,-2181.03 703.4,-2188.53 708.65,-2188.53"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="635.44,-2212.36 635.44,-2235.16 706.02,-2235.16 706.02,-2212.36 635.44,-2212.36"/>
<text xml:space="preserve" text-anchor="start" x="638.44" y="-2219.56" font-family="Arial" font-size="14.00" fill="#c9c9c9">H3 utilities</text>
</g>
</g>
</svg>
`;case"runtimeFlow":return`<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
 "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<!-- Generated by graphviz version 14.0.4 (0)
 -->
<!-- Pages: 1 -->
<svg width="1738pt" height="1236pt"
 viewBox="0.00 0.00 1738.00 1236.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(15.05 1220.65)">
<g id="clust1" class="cluster">
<title>cluster_h3routingplatform</title>
<polygon fill="#0d4b6c" stroke="#0b3c57" points="407.89,-8 407.89,-934.8 1699.89,-934.8 1699.89,-8 407.89,-8"/>
<text xml:space="preserve" text-anchor="start" x="415.89" y="-921.9" font-family="Arial" font-weight="bold" font-size="11.00" fill="#b6ecf7" fill-opacity="0.701961">H3 ROUTING PLATFORM</text>
</g>
<!-- streamlitui -->
<g id="node1" class="node">
<title>streamlitui</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="779.87,-873.6 447.9,-873.6 447.9,-693.6 779.87,-693.6 779.87,-873.6"/>
<text xml:space="preserve" text-anchor="start" x="561.66" y="-807.4" font-family="Arial" font-size="20.00" fill="#eff6ff">Streamlit UI</text>
<text xml:space="preserve" text-anchor="start" x="562.59" y="-785.7" font-family="Arial" font-size="13.00" fill="#bfdbfe">Python / Streamlit</text>
<text xml:space="preserve" text-anchor="start" x="467.96" y="-764.3" font-family="Arial" font-size="15.00" fill="#bfdbfe">Interactive map visualization and debugging</text>
<text xml:space="preserve" text-anchor="start" x="585.12" y="-746.3" font-family="Arial" font-size="15.00" fill="#bfdbfe">interface</text>
</g>
<!-- pythonsdk -->
<g id="node2" class="node">
<title>pythonsdk</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1215.93,-873.6 889.85,-873.6 889.85,-693.6 1215.93,-693.6 1215.93,-873.6"/>
<text xml:space="preserve" text-anchor="start" x="998.42" y="-807.4" font-family="Arial" font-size="20.00" fill="#eff6ff">Python SDK</text>
<text xml:space="preserve" text-anchor="start" x="1032.65" y="-785.7" font-family="Arial" font-size="13.00" fill="#bfdbfe">Python</text>
<text xml:space="preserve" text-anchor="start" x="909.9" y="-764.3" font-family="Arial" font-size="15.00" fill="#bfdbfe">h3&#45;routing&#45;client package for programmatic</text>
<text xml:space="preserve" text-anchor="start" x="1029.55" y="-746.3" font-family="Arial" font-size="15.00" fill="#bfdbfe">access</text>
</g>
<!-- duckdb -->
<g id="node3" class="node">
<title>duckdb</title>
<path fill="#64748b" stroke="#475569" stroke-width="2" d="M1659.7,-857.24C1659.7,-866.27 1584.93,-873.6 1492.89,-873.6 1400.84,-873.6 1326.07,-866.27 1326.07,-857.24 1326.07,-857.24 1326.07,-709.96 1326.07,-709.96 1326.07,-700.93 1400.84,-693.6 1492.89,-693.6 1584.93,-693.6 1659.7,-700.93 1659.7,-709.96 1659.7,-709.96 1659.7,-857.24 1659.7,-857.24"/>
<path fill="none" stroke="#475569" stroke-width="2" d="M1659.7,-857.24C1659.7,-848.21 1584.93,-840.87 1492.89,-840.87 1400.84,-840.87 1326.07,-848.21 1326.07,-857.24"/>
<text xml:space="preserve" text-anchor="start" x="1410.63" y="-797.6" font-family="Arial" font-size="20.00" fill="#f8fafc">DuckDB Database</text>
<text xml:space="preserve" text-anchor="start" x="1346.13" y="-774.1" font-family="Arial" font-size="15.00" fill="#cbd5e1">Stores edges, nodes, shortcuts, and dataset</text>
<text xml:space="preserve" text-anchor="start" x="1480.8" y="-756.1" font-family="Arial" font-size="15.00" fill="#cbd5e1">info</text>
</g>
<!-- apigateway -->
<g id="node4" class="node">
<title>apigateway</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1220.95,-550.8 884.83,-550.8 884.83,-370.8 1220.95,-370.8 1220.95,-550.8"/>
<text xml:space="preserve" text-anchor="start" x="994.53" y="-484.6" font-family="Arial" font-size="20.00" fill="#eff6ff">API Gateway</text>
<text xml:space="preserve" text-anchor="start" x="1004.12" y="-462.9" font-family="Arial" font-size="13.00" fill="#bfdbfe">Python / FastAPI</text>
<text xml:space="preserve" text-anchor="start" x="904.88" y="-441.5" font-family="Arial" font-size="15.00" fill="#bfdbfe">REST API on port 8000, coordinates dataset</text>
<text xml:space="preserve" text-anchor="start" x="950.32" y="-423.5" font-family="Arial" font-size="15.00" fill="#bfdbfe">loading and request translation</text>
</g>
<!-- cppengine -->
<g id="node5" class="node">
<title>cppengine</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1230.11,-228 875.66,-228 875.66,-48 1230.11,-48 1230.11,-228"/>
<text xml:space="preserve" text-anchor="start" x="962.82" y="-161.8" font-family="Arial" font-size="20.00" fill="#eff6ff">C++ Routing Engine</text>
<text xml:space="preserve" text-anchor="start" x="1001.24" y="-140.1" font-family="Arial" font-size="13.00" fill="#bfdbfe">C++ / Crow HTTP</text>
<text xml:space="preserve" text-anchor="start" x="895.72" y="-118.7" font-family="Arial" font-size="15.00" fill="#bfdbfe">High&#45;performance engine on port 8082 with CH</text>
<text xml:space="preserve" text-anchor="start" x="1018.29" y="-100.7" font-family="Arial" font-size="15.00" fill="#bfdbfe">algorithms</text>
</g>
<!-- developer -->
<g id="node6" class="node">
<title>developer</title>
<polygon fill="#a35829" stroke="#7e451d" stroke-width="0" points="1003.84,-1205.6 661.93,-1205.6 661.93,-1025.6 1003.84,-1025.6 1003.84,-1205.6"/>
<text xml:space="preserve" text-anchor="start" x="787.31" y="-1129.6" font-family="Arial" font-size="20.00" fill="#ffe0c2">Developer</text>
<text xml:space="preserve" text-anchor="start" x="681.99" y="-1106.1" font-family="Arial" font-size="15.00" fill="#f9b27c">Uses Streamlit UI for testing and Python SDK</text>
<text xml:space="preserve" text-anchor="start" x="787.03" y="-1088.1" font-family="Arial" font-size="15.00" fill="#f9b27c">for integration</text>
</g>
<!-- externalclient -->
<g id="node7" class="node">
<title>externalclient</title>
<polygon fill="#a35829" stroke="#7e451d" stroke-width="0" points="337.78,-873.6 0,-873.6 0,-693.6 337.78,-693.6 337.78,-873.6"/>
<text xml:space="preserve" text-anchor="start" x="103.86" y="-797.6" font-family="Arial" font-size="20.00" fill="#ffe0c2">External Client</text>
<text xml:space="preserve" text-anchor="start" x="20.06" y="-774.1" font-family="Arial" font-size="15.00" fill="#f9b27c">Any application consuming the routing REST</text>
<text xml:space="preserve" text-anchor="start" x="156.8" y="-756.1" font-family="Arial" font-size="15.00" fill="#f9b27c">API</text>
</g>
<!-- streamlitui&#45;&gt;apigateway -->
<g id="edge4" class="edge">
<title>streamlitui&#45;&gt;apigateway</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M735.59,-693.67C793.88,-651.07 863.73,-600.03 923.03,-556.69"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="924.38,-558.96 928.88,-552.42 921.28,-554.72 924.38,-558.96"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="846.55,-610.8 846.55,-633.6 946.69,-633.6 946.69,-610.8 846.55,-610.8"/>
<text xml:space="preserve" text-anchor="start" x="849.55" y="-618" font-family="Arial" font-size="14.00" fill="#c9c9c9">HTTP requests</text>
</g>
<!-- pythonsdk&#45;&gt;apigateway -->
<g id="edge5" class="edge">
<title>pythonsdk&#45;&gt;apigateway</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1052.89,-693.67C1052.89,-652.47 1052.89,-603.36 1052.89,-560.97"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1055.51,-561.16 1052.89,-553.66 1050.26,-561.16 1055.51,-561.16"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1052.89,-610.8 1052.89,-633.6 1153.03,-633.6 1153.03,-610.8 1052.89,-610.8"/>
<text xml:space="preserve" text-anchor="start" x="1055.89" y="-618" font-family="Arial" font-size="14.00" fill="#c9c9c9">HTTP requests</text>
</g>
<!-- duckdb&#45;&gt;cppengine -->
<g id="edge6" class="edge">
<title>duckdb&#45;&gt;cppengine</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1462.22,-693C1423.34,-588.18 1348.77,-413.1 1245.89,-288 1230.35,-269.11 1211.99,-251.15 1192.88,-234.67"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1194.67,-232.75 1187.25,-229.9 1191.28,-236.75 1194.67,-232.75"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1400.26,-449.4 1400.26,-472.2 1506.65,-472.2 1506.65,-449.4 1400.26,-449.4"/>
<text xml:space="preserve" text-anchor="start" x="1403.26" y="-456.6" font-family="Arial" font-size="14.00" fill="#c9c9c9">Loads at startup</text>
</g>
<!-- apigateway&#45;&gt;cppengine -->
<g id="edge7" class="edge">
<title>apigateway&#45;&gt;cppengine</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1052.89,-370.87C1052.89,-329.67 1052.89,-280.56 1052.89,-238.17"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1055.51,-238.36 1052.89,-230.86 1050.26,-238.36 1055.51,-238.36"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1052.89,-288 1052.89,-310.8 1218.42,-310.8 1218.42,-288 1052.89,-288"/>
<text xml:space="preserve" text-anchor="start" x="1055.89" y="-295.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">Route queries (port 8082)</text>
</g>
<!-- developer&#45;&gt;streamlitui -->
<g id="edge1" class="edge">
<title>developer&#45;&gt;streamlitui</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M771.35,-1025.85C757.83,-1006.09 743.65,-985.19 730.61,-965.6 712.67,-938.63 693.5,-909.19 676,-882.04"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="678.28,-880.74 672.01,-875.86 673.87,-883.58 678.28,-880.74"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="730.61,-942.8 730.61,-965.6 868.89,-965.6 868.89,-942.8 730.61,-942.8"/>
<text xml:space="preserve" text-anchor="start" x="733.61" y="-950" font-family="Arial" font-size="14.00" fill="#c9c9c9">Uses for visualization</text>
</g>
<!-- developer&#45;&gt;pythonsdk -->
<g id="edge2" class="edge">
<title>developer&#45;&gt;pythonsdk</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M892.13,-1025.73C921.72,-981.34 957.59,-927.54 987.93,-882.03"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="990.07,-883.56 992.05,-875.86 985.7,-880.64 990.07,-883.56"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="942.89,-942.8 942.89,-965.6 1032.94,-965.6 1032.94,-942.8 942.89,-942.8"/>
<text xml:space="preserve" text-anchor="start" x="945.89" y="-950" font-family="Arial" font-size="14.00" fill="#c9c9c9">Integrates via</text>
</g>
<!-- externalclient&#45;&gt;apigateway -->
<g id="edge3" class="edge">
<title>externalclient&#45;&gt;apigateway</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M337.72,-710.56C352.28,-704.7 366.81,-698.98 380.89,-693.6 547.1,-630.12 739.22,-564.63 875.36,-519.52"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="875.89,-522.11 882.19,-517.26 874.24,-517.12 875.89,-522.11"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="601.17,-610.8 601.17,-633.6 702.86,-633.6 702.86,-610.8 601.17,-610.8"/>
<text xml:space="preserve" text-anchor="start" x="604.17" y="-618" font-family="Arial" font-size="14.00" fill="#c9c9c9">REST API calls</text>
</g>
</g>
</svg>
`;case"engineComponents":return`<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
 "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<!-- Generated by graphviz version 14.0.4 (0)
 -->
<!-- Pages: 1 -->
<svg width="1322pt" height="650pt"
 viewBox="0.00 0.00 1322.00 650.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(15.05 635.05)">
<g id="clust1" class="cluster">
<title>cluster_cppengine</title>
<polygon fill="#194b9e" stroke="#1b3d88" points="8,-8 8,-612 1284,-612 1284,-8 8,-8"/>
<text xml:space="preserve" text-anchor="start" x="16" y="-599.1" font-family="Arial" font-weight="bold" font-size="11.00" fill="#bfdbfe" fill-opacity="0.701961">C++ ROUTING ENGINE</text>
</g>
<!-- queryalgorithms -->
<g id="node1" class="node">
<title>queryalgorithms</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="810.02,-550.8 489.98,-550.8 489.98,-370.8 810.02,-370.8 810.02,-550.8"/>
<text xml:space="preserve" text-anchor="start" x="577.75" y="-474.8" font-family="Arial" font-size="20.00" fill="#eef2ff">queryAlgorithms</text>
<text xml:space="preserve" text-anchor="start" x="549.54" y="-451.3" font-family="Arial" font-size="15.00" fill="#c7d2fe">Dijkstra, Bidirectional, Pruned,</text>
<text xml:space="preserve" text-anchor="start" x="591.64" y="-433.3" font-family="Arial" font-size="15.00" fill="#c7d2fe">Unidirectional CH</text>
</g>
<!-- spatialindex -->
<g id="node2" class="node">
<title>spatialindex</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="1244.22,-550.8 919.78,-550.8 919.78,-370.8 1244.22,-370.8 1244.22,-550.8"/>
<text xml:space="preserve" text-anchor="start" x="1028.63" y="-465.8" font-family="Arial" font-size="20.00" fill="#eef2ff">spatialIndex</text>
<text xml:space="preserve" text-anchor="start" x="939.84" y="-442.3" font-family="Arial" font-size="15.00" fill="#c7d2fe">H3 or R&#45;tree index for nearest edge lookup</text>
</g>
<!-- csrgraph -->
<g id="node3" class="node">
<title>csrgraph</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="381.78,-228 48.22,-228 48.22,-48 381.78,-48 381.78,-228"/>
<text xml:space="preserve" text-anchor="start" x="173.88" y="-152" font-family="Arial" font-size="20.00" fill="#eef2ff">csrGraph</text>
<text xml:space="preserve" text-anchor="start" x="68.28" y="-128.5" font-family="Arial" font-size="15.00" fill="#c7d2fe">Compressed Sparse Row graph for memory</text>
<text xml:space="preserve" text-anchor="start" x="183.74" y="-110.5" font-family="Arial" font-size="15.00" fill="#c7d2fe">efficiency</text>
</g>
<!-- pathexpander -->
<g id="node4" class="node">
<title>pathexpander</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="812.02,-228 491.98,-228 491.98,-48 812.02,-48 812.02,-228"/>
<text xml:space="preserve" text-anchor="start" x="589.73" y="-152" font-family="Arial" font-size="20.00" fill="#eef2ff">pathExpander</text>
<text xml:space="preserve" text-anchor="start" x="526.51" y="-128.5" font-family="Arial" font-size="15.00" fill="#c7d2fe">Resolves shortcut paths to base edge</text>
<text xml:space="preserve" text-anchor="start" x="615.72" y="-110.5" font-family="Arial" font-size="15.00" fill="#c7d2fe">sequences</text>
</g>
<!-- shortcutgraph -->
<g id="node5" class="node">
<title>shortcutgraph</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="1242.02,-228 921.98,-228 921.98,-48 1242.02,-48 1242.02,-228"/>
<text xml:space="preserve" text-anchor="start" x="1018.64" y="-152" font-family="Arial" font-size="20.00" fill="#eef2ff">shortcutGraph</text>
<text xml:space="preserve" text-anchor="start" x="943.6" y="-128.5" font-family="Arial" font-size="15.00" fill="#c7d2fe">Graph with adjacency lists, shortcuts, and</text>
<text xml:space="preserve" text-anchor="start" x="1031.96" y="-110.5" font-family="Arial" font-size="15.00" fill="#c7d2fe">edge metadata</text>
</g>
<!-- queryalgorithms&#45;&gt;csrgraph -->
<g id="edge1" class="edge">
<title>queryalgorithms&#45;&gt;csrgraph</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M529.41,-370.87C471.65,-328.27 402.44,-277.23 343.67,-233.89"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="345.48,-231.97 337.89,-229.63 342.37,-236.19 345.48,-231.97"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="445.54,-288 445.54,-310.8 500.56,-310.8 500.56,-288 445.54,-288"/>
<text xml:space="preserve" text-anchor="start" x="448.54" y="-295.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">Queries</text>
</g>
<!-- queryalgorithms&#45;&gt;pathexpander -->
<g id="edge2" class="edge">
<title>queryalgorithms&#45;&gt;pathexpander</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M643.02,-371.09C641.66,-344.39 640.91,-315.01 641.83,-288 642.38,-271.91 643.26,-254.85 644.28,-238.25"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="646.88,-238.65 644.74,-231 641.64,-238.32 646.88,-238.65"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="641.83,-288 641.83,-310.8 763,-310.8 763,-288 641.83,-288"/>
<text xml:space="preserve" text-anchor="start" x="644.83" y="-295.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">Expands shortcuts</text>
</g>
<!-- queryalgorithms&#45;&gt;shortcutgraph -->
<g id="edge3" class="edge">
<title>queryalgorithms&#45;&gt;shortcutgraph</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M769.76,-370.87C827.12,-328.27 895.85,-277.23 954.22,-233.89"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="955.49,-236.21 959.95,-229.63 952.36,-232 955.49,-236.21"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="878.95,-288 878.95,-310.8 933.97,-310.8 933.97,-288 878.95,-288"/>
<text xml:space="preserve" text-anchor="start" x="881.95" y="-295.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">Queries</text>
</g>
<!-- spatialindex&#45;&gt;shortcutgraph -->
<g id="edge4" class="edge">
<title>spatialindex&#45;&gt;shortcutgraph</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1082,-370.87C1082,-329.67 1082,-280.56 1082,-238.17"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1084.63,-238.36 1082,-230.86 1079.38,-238.36 1084.63,-238.36"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1082,-288 1082,-310.8 1179.07,-310.8 1179.07,-288 1082,-288"/>
<text xml:space="preserve" text-anchor="start" x="1085" y="-295.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">Indexes edges</text>
</g>
</g>
</svg>
`;case"apiGatewayComponents":return`<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
 "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<!-- Generated by graphviz version 14.0.4 (0)
 -->
<!-- Pages: 1 -->
<svg width="912pt" height="650pt"
 viewBox="0.00 0.00 912.00 650.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(15.05 635.05)">
<g id="clust1" class="cluster">
<title>cluster_apigateway</title>
<polygon fill="#194b9e" stroke="#1b3d88" points="8,-8 8,-612 874,-612 874,-8 8,-8"/>
<text xml:space="preserve" text-anchor="start" x="16" y="-599.1" font-family="Arial" font-weight="bold" font-size="11.00" fill="#bfdbfe" fill-opacity="0.701961">API GATEWAY</text>
</g>
<!-- routehandler -->
<g id="node1" class="node">
<title>routehandler</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="561.4,-550.8 208.6,-550.8 208.6,-370.8 561.4,-370.8 561.4,-550.8"/>
<text xml:space="preserve" text-anchor="start" x="327.19" y="-465.8" font-family="Arial" font-size="20.00" fill="#eef2ff">routeHandler</text>
<text xml:space="preserve" text-anchor="start" x="228.65" y="-442.3" font-family="Arial" font-size="15.00" fill="#c7d2fe">Validates requests and forwards to C++ engine</text>
</g>
<!-- datasetregistry -->
<g id="node2" class="node">
<title>datasetregistry</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="404.47,-228 47.53,-228 47.53,-48 404.47,-48 404.47,-228"/>
<text xml:space="preserve" text-anchor="start" x="156.52" y="-143" font-family="Arial" font-size="20.00" fill="#eef2ff">datasetRegistry</text>
<text xml:space="preserve" text-anchor="start" x="67.58" y="-119.5" font-family="Arial" font-size="15.00" fill="#c7d2fe">Manages available datasets from datasets.yaml</text>
</g>
<!-- coordtranslator -->
<g id="node3" class="node">
<title>coordtranslator</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="834.02,-228 513.98,-228 513.98,-48 834.02,-48 834.02,-228"/>
<text xml:space="preserve" text-anchor="start" x="603.97" y="-152" font-family="Arial" font-size="20.00" fill="#eef2ff">coordTranslator</text>
<text xml:space="preserve" text-anchor="start" x="548.51" y="-128.5" font-family="Arial" font-size="15.00" fill="#c7d2fe">Converts lat/lon to graph edge IDs via</text>
<text xml:space="preserve" text-anchor="start" x="632.31" y="-110.5" font-family="Arial" font-size="15.00" fill="#c7d2fe">spatial index</text>
</g>
<!-- routehandler&#45;&gt;datasetregistry -->
<g id="edge1" class="edge">
<title>routehandler&#45;&gt;datasetregistry</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M340.92,-370.87C320.33,-329.32 295.75,-279.73 274.62,-237.1"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="277.05,-236.1 271.37,-230.54 272.35,-238.43 277.05,-236.1"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="310.27,-288 310.27,-310.8 386.3,-310.8 386.3,-288 310.27,-288"/>
<text xml:space="preserve" text-anchor="start" x="313.27" y="-295.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">Loads from</text>
</g>
<!-- routehandler&#45;&gt;coordtranslator -->
<g id="edge2" class="edge">
<title>routehandler&#45;&gt;coordtranslator</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M465.12,-370.87C503.02,-328.8 548.34,-278.48 587.07,-235.49"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="588.88,-237.41 591.95,-230.08 584.98,-233.89 588.88,-237.41"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="538.17,-288 538.17,-310.8 576.06,-310.8 576.06,-288 538.17,-288"/>
<text xml:space="preserve" text-anchor="start" x="541.17" y="-295.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">Uses</text>
</g>
</g>
</svg>
`;case"shortcutPhases":return`<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
 "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<!-- Generated by graphviz version 14.0.4 (0)
 -->
<!-- Pages: 1 -->
<svg width="927pt" height="2216pt"
 viewBox="0.00 0.00 927.00 2216.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(15.05 2201.05)">
<g id="clust1" class="cluster">
<title>cluster_shortcutgenerator</title>
<polygon fill="#194b9e" stroke="#1b3d88" points="8,-282.8 8,-2178 889,-2178 889,-282.8 8,-282.8"/>
<text xml:space="preserve" text-anchor="start" x="16" y="-2165.1" font-family="Arial" font-weight="bold" font-size="11.00" fill="#bfdbfe" fill-opacity="0.701961">SHORTCUT GENERATOR</text>
</g>
<!-- dataloader -->
<g id="node1" class="node">
<title>dataloader</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="504.58,-2116.8 143.42,-2116.8 143.42,-1936.8 504.58,-1936.8 504.58,-2116.8"/>
<text xml:space="preserve" text-anchor="start" x="273.4" y="-2040.8" font-family="Arial" font-size="20.00" fill="#eef2ff">dataLoader</text>
<text xml:space="preserve" text-anchor="start" x="163.48" y="-2017.3" font-family="Arial" font-size="15.00" fill="#c7d2fe">Loads edges and edge_graph from DuckDB into</text>
<text xml:space="preserve" text-anchor="start" x="276.06" y="-1999.3" font-family="Arial" font-size="15.00" fill="#c7d2fe">working tables</text>
</g>
<!-- phase1 -->
<g id="node2" class="node">
<title>phase1</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="485.38,-1794 162.62,-1794 162.62,-1614 485.38,-1614 485.38,-1794"/>
<text xml:space="preserve" text-anchor="start" x="202.27" y="-1718" font-family="Arial" font-size="20.00" fill="#eef2ff">Phase 1: Forward Chunked</text>
<text xml:space="preserve" text-anchor="start" x="182.68" y="-1694.5" font-family="Arial" font-size="15.00" fill="#c7d2fe">Processes res 15→7 in parallel chunks per</text>
<text xml:space="preserve" text-anchor="start" x="283.98" y="-1676.5" font-family="Arial" font-size="15.00" fill="#c7d2fe">partition cell</text>
</g>
<!-- cellassigner -->
<g id="node3" class="node">
<title>cellassigner</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="394.54,-1471.2 63.46,-1471.2 63.46,-1291.2 394.54,-1291.2 394.54,-1471.2"/>
<text xml:space="preserve" text-anchor="start" x="175.09" y="-1395.2" font-family="Arial" font-size="20.00" fill="#eef2ff">cellAssigner</text>
<text xml:space="preserve" text-anchor="start" x="83.51" y="-1371.7" font-family="Arial" font-size="15.00" fill="#c7d2fe">Assigns shortcuts to H3 cells based on LCA</text>
<text xml:space="preserve" text-anchor="start" x="196.48" y="-1353.7" font-family="Arial" font-size="15.00" fill="#c7d2fe">resolution</text>
</g>
<!-- phase2 -->
<g id="node4" class="node">
<title>phase2</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="843.38,-1471.2 510.62,-1471.2 510.62,-1291.2 843.38,-1291.2 843.38,-1471.2"/>
<text xml:space="preserve" text-anchor="start" x="534.7" y="-1395.2" font-family="Arial" font-size="20.00" fill="#eef2ff">Phase 2: Forward Consolidation</text>
<text xml:space="preserve" text-anchor="start" x="530.67" y="-1371.7" font-family="Arial" font-size="15.00" fill="#c7d2fe">Merges cells upward res 6→0, deduplicating</text>
<text xml:space="preserve" text-anchor="start" x="651.57" y="-1353.7" font-family="Arial" font-size="15.00" fill="#c7d2fe">via cost</text>
</g>
<!-- shortestpathsolver -->
<g id="node5" class="node">
<title>shortestpathsolver</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="399.53,-1148.4 48.47,-1148.4 48.47,-968.4 399.53,-968.4 399.53,-1148.4"/>
<text xml:space="preserve" text-anchor="start" x="139.51" y="-1072.4" font-family="Arial" font-size="20.00" fill="#eef2ff">shortestPathSolver</text>
<text xml:space="preserve" text-anchor="start" x="68.53" y="-1048.9" font-family="Arial" font-size="15.00" fill="#c7d2fe">Computes optimal shortcuts via SciPy/DuckDB</text>
<text xml:space="preserve" text-anchor="start" x="168.14" y="-1030.9" font-family="Arial" font-size="15.00" fill="#c7d2fe">graph algorithms</text>
</g>
<!-- phase3 -->
<g id="node6" class="node">
<title>phase3</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="848.59,-1148.4 509.41,-1148.4 509.41,-968.4 848.59,-968.4 848.59,-1148.4"/>
<text xml:space="preserve" text-anchor="start" x="529.47" y="-1072.4" font-family="Arial" font-size="20.00" fill="#eef2ff">Phase 3: Backward Consolidation</text>
<text xml:space="preserve" text-anchor="start" x="576.04" y="-1048.9" font-family="Arial" font-size="15.00" fill="#c7d2fe">Splits cells downward res 0→7,</text>
<text xml:space="preserve" text-anchor="start" x="600.63" y="-1030.9" font-family="Arial" font-size="15.00" fill="#c7d2fe">re&#45;partitioning shortcuts</text>
</g>
<!-- deduplicator -->
<g id="node7" class="node">
<title>deduplicator</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="409.97,-825.6 48.03,-825.6 48.03,-645.6 409.97,-645.6 409.97,-825.6"/>
<text xml:space="preserve" text-anchor="start" x="174.52" y="-749.6" font-family="Arial" font-size="20.00" fill="#eef2ff">deduplicator</text>
<text xml:space="preserve" text-anchor="start" x="68.09" y="-726.1" font-family="Arial" font-size="15.00" fill="#c7d2fe">Removes redundant shortcuts keeping minimum</text>
<text xml:space="preserve" text-anchor="start" x="215.25" y="-708.1" font-family="Arial" font-size="15.00" fill="#c7d2fe">cost</text>
</g>
<!-- phase4 -->
<g id="node8" class="node">
<title>phase4</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="840.02,-825.6 519.98,-825.6 519.98,-645.6 840.02,-645.6 840.02,-825.6"/>
<text xml:space="preserve" text-anchor="start" x="551.04" y="-749.6" font-family="Arial" font-size="20.00" fill="#eef2ff">Phase 4: Backward Chunked</text>
<text xml:space="preserve" text-anchor="start" x="549.52" y="-726.1" font-family="Arial" font-size="15.00" fill="#c7d2fe">Processes res 8→15 in parallel chunks,</text>
<text xml:space="preserve" text-anchor="start" x="602.88" y="-708.1" font-family="Arial" font-size="15.00" fill="#c7d2fe">finalizing all resolutions</text>
</g>
<!-- finalizer -->
<g id="node9" class="node">
<title>finalizer</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="848.71,-502.8 499.29,-502.8 499.29,-322.8 848.71,-322.8 848.71,-502.8"/>
<text xml:space="preserve" text-anchor="start" x="639.54" y="-426.8" font-family="Arial" font-size="20.00" fill="#eef2ff">finalizer</text>
<text xml:space="preserve" text-anchor="start" x="519.34" y="-403.3" font-family="Arial" font-size="15.00" fill="#c7d2fe">Exports final shortcuts to Parquet and DuckDB</text>
<text xml:space="preserve" text-anchor="start" x="647.74" y="-385.3" font-family="Arial" font-size="15.00" fill="#c7d2fe">schema</text>
</g>
<!-- duckdb -->
<g id="node10" class="node">
<title>duckdb</title>
<path fill="#64748b" stroke="#475569" stroke-width="2" d="M840.82,-163.64C840.82,-172.67 766.05,-180 674,-180 581.95,-180 507.18,-172.67 507.18,-163.64 507.18,-163.64 507.18,-16.36 507.18,-16.36 507.18,-7.33 581.95,0 674,0 766.05,0 840.82,-7.33 840.82,-16.36 840.82,-16.36 840.82,-163.64 840.82,-163.64"/>
<path fill="none" stroke="#475569" stroke-width="2" d="M840.82,-163.64C840.82,-154.61 766.05,-147.27 674,-147.27 581.95,-147.27 507.18,-154.61 507.18,-163.64"/>
<text xml:space="preserve" text-anchor="start" x="591.74" y="-104" font-family="Arial" font-size="20.00" fill="#f8fafc">DuckDB Database</text>
<text xml:space="preserve" text-anchor="start" x="527.24" y="-80.5" font-family="Arial" font-size="15.00" fill="#cbd5e1">Stores edges, nodes, shortcuts, and dataset</text>
<text xml:space="preserve" text-anchor="start" x="661.91" y="-62.5" font-family="Arial" font-size="15.00" fill="#cbd5e1">info</text>
</g>
<!-- dataloader&#45;&gt;phase1 -->
<g id="edge1" class="edge">
<title>dataloader&#45;&gt;phase1</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M324,-1936.87C324,-1895.67 324,-1846.56 324,-1804.17"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="326.63,-1804.36 324,-1796.86 321.38,-1804.36 326.63,-1804.36"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="324,-1854 324,-1876.8 410.18,-1876.8 410.18,-1854 324,-1854"/>
<text xml:space="preserve" text-anchor="start" x="327" y="-1861.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">Loads edges</text>
</g>
<!-- phase1&#45;&gt;cellassigner -->
<g id="edge2" class="edge">
<title>phase1&#45;&gt;cellassigner</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M297.66,-1614.07C285.44,-1572.78 270.86,-1523.55 258.29,-1481.1"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="260.81,-1480.38 256.17,-1473.93 255.78,-1481.87 260.81,-1480.38"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="279.35,-1531.2 279.35,-1554 360.83,-1554 360.83,-1531.2 279.35,-1531.2"/>
<text xml:space="preserve" text-anchor="start" x="282.35" y="-1538.4" font-family="Arial" font-size="14.00" fill="#c9c9c9">Per iteration</text>
</g>
<!-- phase1&#45;&gt;phase2 -->
<g id="edge3" class="edge">
<title>phase1&#45;&gt;phase2</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M421.86,-1614.07C468.44,-1571.73 524.21,-1521.06 571.7,-1477.89"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="573.23,-1480.05 577.01,-1473.07 569.7,-1476.17 573.23,-1480.05"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="511.08,-1531.2 511.08,-1554 622.94,-1554 622.94,-1531.2 511.08,-1531.2"/>
<text xml:space="preserve" text-anchor="start" x="514.08" y="-1538.4" font-family="Arial" font-size="14.00" fill="#c9c9c9">Chunked outputs</text>
</g>
<!-- cellassigner&#45;&gt;shortestpathsolver -->
<g id="edge4" class="edge">
<title>cellassigner&#45;&gt;shortestpathsolver</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M227.61,-1291.27C226.97,-1250.07 226.21,-1200.96 225.55,-1158.57"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="228.17,-1158.71 225.43,-1151.26 222.92,-1158.8 228.17,-1158.71"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="226.65,-1208.4 226.65,-1231.2 331.46,-1231.2 331.46,-1208.4 226.65,-1208.4"/>
<text xml:space="preserve" text-anchor="start" x="229.65" y="-1215.6" font-family="Arial" font-size="14.00" fill="#c9c9c9">Active shortcuts</text>
</g>
<!-- phase2&#45;&gt;phase3 -->
<g id="edge5" class="edge">
<title>phase2&#45;&gt;phase3</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M677.55,-1291.27C677.81,-1250.07 678.12,-1200.96 678.38,-1158.57"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="681.01,-1158.77 678.43,-1151.26 675.76,-1158.74 681.01,-1158.77"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="678.06,-1208.4 678.06,-1231.2 816.36,-1231.2 816.36,-1208.4 678.06,-1208.4"/>
<text xml:space="preserve" text-anchor="start" x="681.06" y="-1215.6" font-family="Arial" font-size="14.00" fill="#c9c9c9">Consolidated to res 0</text>
</g>
<!-- shortestpathsolver&#45;&gt;deduplicator -->
<g id="edge6" class="edge">
<title>shortestpathsolver&#45;&gt;deduplicator</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M225.39,-968.47C226.03,-927.27 226.79,-878.16 227.45,-835.77"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="230.08,-836 227.57,-828.46 224.83,-835.91 230.08,-836"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="226.65,-885.6 226.65,-908.4 319.02,-908.4 319.02,-885.6 226.65,-885.6"/>
<text xml:space="preserve" text-anchor="start" x="229.65" y="-892.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">Optimal paths</text>
</g>
<!-- phase3&#45;&gt;phase4 -->
<g id="edge7" class="edge">
<title>phase3&#45;&gt;phase4</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M679.28,-968.47C679.41,-927.27 679.56,-878.16 679.69,-835.77"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="682.32,-835.96 679.71,-828.46 677.07,-835.95 682.32,-835.96"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="679.53,-885.6 679.53,-908.4 773.47,-908.4 773.47,-885.6 679.53,-885.6"/>
<text xml:space="preserve" text-anchor="start" x="682.53" y="-892.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">Re&#45;partitioned</text>
</g>
<!-- phase4&#45;&gt;finalizer -->
<g id="edge8" class="edge">
<title>phase4&#45;&gt;finalizer</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M678.34,-645.67C677.57,-604.47 676.65,-555.36 675.85,-512.97"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="678.48,-513.11 675.72,-505.66 673.23,-513.2 678.48,-513.11"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="677.18,-562.8 677.18,-585.6 805.37,-585.6 805.37,-562.8 677.18,-562.8"/>
<text xml:space="preserve" text-anchor="start" x="680.18" y="-570" font-family="Arial" font-size="14.00" fill="#c9c9c9">All resolutions done</text>
</g>
<!-- finalizer&#45;&gt;duckdb -->
<g id="edge9" class="edge">
<title>finalizer&#45;&gt;duckdb</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M674,-322.87C674,-282.01 674,-233.38 674,-191.23"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="676.63,-191.47 674,-183.97 671.38,-191.47 676.63,-191.47"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="674,-240 674,-262.8 833.26,-262.8 833.26,-240 674,-240"/>
<text xml:space="preserve" text-anchor="start" x="677" y="-247.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">Writes shortcuts schema</text>
</g>
</g>
</svg>
`;case"duckOSMComponents":return`<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
 "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<!-- Generated by graphviz version 14.0.4 (0)
 -->
<!-- Pages: 1 -->
<svg width="452pt" height="2910pt"
 viewBox="0.00 0.00 452.00 2910.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(15.05 2894.65)">
<g id="clust1" class="cluster">
<title>cluster_duckosm</title>
<polygon fill="#194b9e" stroke="#1b3d88" points="8,-8 8,-2871.6 414,-2871.6 414,-8 8,-8"/>
<text xml:space="preserve" text-anchor="start" x="16" y="-2858.7" font-family="Arial" font-weight="bold" font-size="11.00" fill="#bfdbfe" fill-opacity="0.701961">DUCKOSM</text>
</g>
<!-- pbfloader -->
<g id="node1" class="node">
<title>pbfloader</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="371.02,-2810.4 50.98,-2810.4 50.98,-2630.4 371.02,-2630.4 371.02,-2810.4"/>
<text xml:space="preserve" text-anchor="start" x="165.96" y="-2725.4" font-family="Arial" font-size="20.00" fill="#eef2ff">pbfLoader</text>
<text xml:space="preserve" text-anchor="start" x="74.28" y="-2701.9" font-family="Arial" font-size="15.00" fill="#c7d2fe">Loads PBF via ST_READOSM extension</text>
</g>
<!-- roadfilter -->
<g id="node2" class="node">
<title>roadfilter</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="371.02,-2487.6 50.98,-2487.6 50.98,-2307.6 371.02,-2307.6 371.02,-2487.6"/>
<text xml:space="preserve" text-anchor="start" x="168.76" y="-2402.6" font-family="Arial" font-size="20.00" fill="#eef2ff">roadFilter</text>
<text xml:space="preserve" text-anchor="start" x="97.62" y="-2379.1" font-family="Arial" font-size="15.00" fill="#c7d2fe">Filters ways to highway types only</text>
</g>
<!-- graphbuilder -->
<g id="node3" class="node">
<title>graphbuilder</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="371.02,-2164.8 50.98,-2164.8 50.98,-1984.8 371.02,-1984.8 371.02,-2164.8"/>
<text xml:space="preserve" text-anchor="start" x="154.3" y="-2079.8" font-family="Arial" font-size="20.00" fill="#eef2ff">graphBuilder</text>
<text xml:space="preserve" text-anchor="start" x="78.03" y="-2056.3" font-family="Arial" font-size="15.00" fill="#c7d2fe">Creates directed edges from OSM ways</text>
</g>
<!-- graphsimplifier -->
<g id="node4" class="node">
<title>graphsimplifier</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="374.46,-1842 47.54,-1842 47.54,-1662 374.46,-1662 374.46,-1842"/>
<text xml:space="preserve" text-anchor="start" x="144.31" y="-1757" font-family="Arial" font-size="20.00" fill="#eef2ff">graphSimplifier</text>
<text xml:space="preserve" text-anchor="start" x="67.59" y="-1733.5" font-family="Arial" font-size="15.00" fill="#c7d2fe">Contracts degree&#45;2 nodes to simplify graph</text>
</g>
<!-- speedprocessor -->
<g id="node5" class="node">
<title>speedprocessor</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="371.02,-1519.2 50.98,-1519.2 50.98,-1339.2 371.02,-1339.2 371.02,-1519.2"/>
<text xml:space="preserve" text-anchor="start" x="138.74" y="-1434.2" font-family="Arial" font-size="20.00" fill="#eef2ff">speedProcessor</text>
<text xml:space="preserve" text-anchor="start" x="87.62" y="-1410.7" font-family="Arial" font-size="15.00" fill="#c7d2fe">Infers speed limits from highway tags</text>
</g>
<!-- costcalculator -->
<g id="node6" class="node">
<title>costcalculator</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="371.02,-1196.4 50.98,-1196.4 50.98,-1016.4 371.02,-1016.4 371.02,-1196.4"/>
<text xml:space="preserve" text-anchor="start" x="147.64" y="-1111.4" font-family="Arial" font-size="20.00" fill="#eef2ff">costCalculator</text>
<text xml:space="preserve" text-anchor="start" x="88.03" y="-1087.9" font-family="Arial" font-size="15.00" fill="#c7d2fe">Calculates travel time costs per edge</text>
</g>
<!-- restrictionprocessor -->
<g id="node7" class="node">
<title>restrictionprocessor</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="371.02,-873.6 50.98,-873.6 50.98,-693.6 371.02,-693.6 371.02,-873.6"/>
<text xml:space="preserve" text-anchor="start" x="122.64" y="-788.6" font-family="Arial" font-size="20.00" fill="#eef2ff">restrictionProcessor</text>
<text xml:space="preserve" text-anchor="start" x="83.05" y="-765.1" font-family="Arial" font-size="15.00" fill="#c7d2fe">Extracts turn restrictions from relations</text>
</g>
<!-- edgegraphbuilder -->
<g id="node8" class="node">
<title>edgegraphbuilder</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="371.02,-550.8 50.98,-550.8 50.98,-370.8 371.02,-370.8 371.02,-550.8"/>
<text xml:space="preserve" text-anchor="start" x="129.83" y="-465.8" font-family="Arial" font-size="20.00" fill="#eef2ff">edgeGraphBuilder</text>
<text xml:space="preserve" text-anchor="start" x="86.75" y="-442.3" font-family="Arial" font-size="15.00" fill="#c7d2fe">Builds edge&#45;to&#45;edge adjacency graph</text>
</g>
<!-- h3indexer -->
<g id="node9" class="node">
<title>h3indexer</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="371.02,-228 50.98,-228 50.98,-48 371.02,-48 371.02,-228"/>
<text xml:space="preserve" text-anchor="start" x="166.52" y="-143" font-family="Arial" font-size="20.00" fill="#eef2ff">h3Indexer</text>
<text xml:space="preserve" text-anchor="start" x="108.02" y="-119.5" font-family="Arial" font-size="15.00" fill="#c7d2fe">Adds H3 cell indexing to edges</text>
</g>
<!-- pbfloader&#45;&gt;roadfilter -->
<g id="edge1" class="edge">
<title>pbfloader&#45;&gt;roadfilter</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M211,-2630.47C211,-2589.27 211,-2540.16 211,-2497.77"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="213.63,-2497.96 211,-2490.46 208.38,-2497.96 213.63,-2497.96"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="211,-2547.6 211,-2570.4 269.12,-2570.4 269.12,-2547.6 211,-2547.6"/>
<text xml:space="preserve" text-anchor="start" x="214" y="-2554.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">Flows to</text>
</g>
<!-- roadfilter&#45;&gt;graphbuilder -->
<g id="edge2" class="edge">
<title>roadfilter&#45;&gt;graphbuilder</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M211,-2307.67C211,-2266.47 211,-2217.36 211,-2174.97"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="213.63,-2175.16 211,-2167.66 208.38,-2175.16 213.63,-2175.16"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="211,-2224.8 211,-2247.6 269.12,-2247.6 269.12,-2224.8 211,-2224.8"/>
<text xml:space="preserve" text-anchor="start" x="214" y="-2232" font-family="Arial" font-size="14.00" fill="#c9c9c9">Flows to</text>
</g>
<!-- graphbuilder&#45;&gt;graphsimplifier -->
<g id="edge3" class="edge">
<title>graphbuilder&#45;&gt;graphsimplifier</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M211,-1984.87C211,-1943.67 211,-1894.56 211,-1852.17"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="213.63,-1852.36 211,-1844.86 208.38,-1852.36 213.63,-1852.36"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="211,-1902 211,-1924.8 269.12,-1924.8 269.12,-1902 211,-1902"/>
<text xml:space="preserve" text-anchor="start" x="214" y="-1909.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">Flows to</text>
</g>
<!-- graphsimplifier&#45;&gt;speedprocessor -->
<g id="edge4" class="edge">
<title>graphsimplifier&#45;&gt;speedprocessor</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M211,-1662.07C211,-1620.87 211,-1571.76 211,-1529.37"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="213.63,-1529.56 211,-1522.06 208.38,-1529.56 213.63,-1529.56"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="211,-1579.2 211,-1602 269.12,-1602 269.12,-1579.2 211,-1579.2"/>
<text xml:space="preserve" text-anchor="start" x="214" y="-1586.4" font-family="Arial" font-size="14.00" fill="#c9c9c9">Flows to</text>
</g>
<!-- speedprocessor&#45;&gt;costcalculator -->
<g id="edge5" class="edge">
<title>speedprocessor&#45;&gt;costcalculator</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M211,-1339.27C211,-1298.07 211,-1248.96 211,-1206.57"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="213.63,-1206.76 211,-1199.26 208.38,-1206.76 213.63,-1206.76"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="211,-1256.4 211,-1279.2 269.12,-1279.2 269.12,-1256.4 211,-1256.4"/>
<text xml:space="preserve" text-anchor="start" x="214" y="-1263.6" font-family="Arial" font-size="14.00" fill="#c9c9c9">Flows to</text>
</g>
<!-- costcalculator&#45;&gt;restrictionprocessor -->
<g id="edge6" class="edge">
<title>costcalculator&#45;&gt;restrictionprocessor</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M211,-1016.47C211,-975.27 211,-926.16 211,-883.77"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="213.63,-883.96 211,-876.46 208.38,-883.96 213.63,-883.96"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="211,-933.6 211,-956.4 269.12,-956.4 269.12,-933.6 211,-933.6"/>
<text xml:space="preserve" text-anchor="start" x="214" y="-940.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">Flows to</text>
</g>
<!-- restrictionprocessor&#45;&gt;edgegraphbuilder -->
<g id="edge7" class="edge">
<title>restrictionprocessor&#45;&gt;edgegraphbuilder</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M211,-693.67C211,-652.47 211,-603.36 211,-560.97"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="213.63,-561.16 211,-553.66 208.38,-561.16 213.63,-561.16"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="211,-610.8 211,-633.6 269.12,-633.6 269.12,-610.8 211,-610.8"/>
<text xml:space="preserve" text-anchor="start" x="214" y="-618" font-family="Arial" font-size="14.00" fill="#c9c9c9">Flows to</text>
</g>
<!-- edgegraphbuilder&#45;&gt;h3indexer -->
<g id="edge8" class="edge">
<title>edgegraphbuilder&#45;&gt;h3indexer</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M211,-370.87C211,-329.67 211,-280.56 211,-238.17"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="213.63,-238.36 211,-230.86 208.38,-238.36 213.63,-238.36"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="211,-288 211,-310.8 269.12,-310.8 269.12,-288 211,-288"/>
<text xml:space="preserve" text-anchor="start" x="214" y="-295.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">Flows to</text>
</g>
</g>
</svg>
`;case"routingSequence":return`<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
 "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<!-- Generated by graphviz version 14.0.4 (0)
 -->
<!-- Pages: 1 -->
<svg width="1400pt" height="1896pt"
 viewBox="0.00 0.00 1400.00 1896.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(15.05 1881.05)">
<g id="clust1" class="cluster">
<title>cluster_h3routingplatform</title>
<polygon fill="#0f4460" stroke="#0d374e" points="8,-8 8,-1595.2 1362,-1595.2 1362,-8 8,-8"/>
<text xml:space="preserve" text-anchor="start" x="16" y="-1582.3" font-family="Arial" font-weight="bold" font-size="11.00" fill="#b6ecf7" fill-opacity="0.701961">H3 ROUTING PLATFORM</text>
</g>
<g id="clust2" class="cluster">
<title>cluster_apigateway</title>
<polygon fill="#194b9e" stroke="#1b3d88" points="48,-681 48,-1285 914,-1285 914,-681 48,-681"/>
<text xml:space="preserve" text-anchor="start" x="56" y="-1272.1" font-family="Arial" font-weight="bold" font-size="11.00" fill="#bfdbfe" fill-opacity="0.701961">API GATEWAY</text>
</g>
<g id="clust3" class="cluster">
<title>cluster_cppengine</title>
<polygon fill="#194b9e" stroke="#1b3d88" points="48,-48 48,-652 1322,-652 1322,-48 48,-48"/>
<text xml:space="preserve" text-anchor="start" x="56" y="-639.1" font-family="Arial" font-weight="bold" font-size="11.00" fill="#bfdbfe" fill-opacity="0.701961">C++ ROUTING ENGINE</text>
</g>
<!-- routehandler -->
<g id="node1" class="node">
<title>routehandler</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="601.4,-1223.8 248.6,-1223.8 248.6,-1043.8 601.4,-1043.8 601.4,-1223.8"/>
<text xml:space="preserve" text-anchor="start" x="367.19" y="-1138.8" font-family="Arial" font-size="20.00" fill="#eef2ff">routeHandler</text>
<text xml:space="preserve" text-anchor="start" x="268.65" y="-1115.3" font-family="Arial" font-size="15.00" fill="#c7d2fe">Validates requests and forwards to C++ engine</text>
</g>
<!-- datasetregistry -->
<g id="node2" class="node">
<title>datasetregistry</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="444.47,-901 87.53,-901 87.53,-721 444.47,-721 444.47,-901"/>
<text xml:space="preserve" text-anchor="start" x="196.52" y="-816" font-family="Arial" font-size="20.00" fill="#eef2ff">datasetRegistry</text>
<text xml:space="preserve" text-anchor="start" x="107.58" y="-792.5" font-family="Arial" font-size="15.00" fill="#c7d2fe">Manages available datasets from datasets.yaml</text>
</g>
<!-- coordtranslator -->
<g id="node3" class="node">
<title>coordtranslator</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="874.02,-901 553.98,-901 553.98,-721 874.02,-721 874.02,-901"/>
<text xml:space="preserve" text-anchor="start" x="643.97" y="-825" font-family="Arial" font-size="20.00" fill="#eef2ff">coordTranslator</text>
<text xml:space="preserve" text-anchor="start" x="588.51" y="-801.5" font-family="Arial" font-size="15.00" fill="#c7d2fe">Converts lat/lon to graph edge IDs via</text>
<text xml:space="preserve" text-anchor="start" x="672.31" y="-783.5" font-family="Arial" font-size="15.00" fill="#c7d2fe">spatial index</text>
</g>
<!-- queryalgorithms -->
<g id="node4" class="node">
<title>queryalgorithms</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="848.02,-590.8 527.98,-590.8 527.98,-410.8 848.02,-410.8 848.02,-590.8"/>
<text xml:space="preserve" text-anchor="start" x="615.75" y="-514.8" font-family="Arial" font-size="20.00" fill="#eef2ff">queryAlgorithms</text>
<text xml:space="preserve" text-anchor="start" x="587.54" y="-491.3" font-family="Arial" font-size="15.00" fill="#c7d2fe">Dijkstra, Bidirectional, Pruned,</text>
<text xml:space="preserve" text-anchor="start" x="629.64" y="-473.3" font-family="Arial" font-size="15.00" fill="#c7d2fe">Unidirectional CH</text>
</g>
<!-- spatialindex -->
<g id="node5" class="node">
<title>spatialindex</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="1282.22,-590.8 957.78,-590.8 957.78,-410.8 1282.22,-410.8 1282.22,-590.8"/>
<text xml:space="preserve" text-anchor="start" x="1066.63" y="-505.8" font-family="Arial" font-size="20.00" fill="#eef2ff">spatialIndex</text>
<text xml:space="preserve" text-anchor="start" x="977.84" y="-482.3" font-family="Arial" font-size="15.00" fill="#c7d2fe">H3 or R&#45;tree index for nearest edge lookup</text>
</g>
<!-- csrgraph -->
<g id="node6" class="node">
<title>csrgraph</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="421.78,-268 88.22,-268 88.22,-88 421.78,-88 421.78,-268"/>
<text xml:space="preserve" text-anchor="start" x="213.88" y="-192" font-family="Arial" font-size="20.00" fill="#eef2ff">csrGraph</text>
<text xml:space="preserve" text-anchor="start" x="108.28" y="-168.5" font-family="Arial" font-size="15.00" fill="#c7d2fe">Compressed Sparse Row graph for memory</text>
<text xml:space="preserve" text-anchor="start" x="223.74" y="-150.5" font-family="Arial" font-size="15.00" fill="#c7d2fe">efficiency</text>
</g>
<!-- pathexpander -->
<g id="node7" class="node">
<title>pathexpander</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="852.02,-268 531.98,-268 531.98,-88 852.02,-88 852.02,-268"/>
<text xml:space="preserve" text-anchor="start" x="629.73" y="-192" font-family="Arial" font-size="20.00" fill="#eef2ff">pathExpander</text>
<text xml:space="preserve" text-anchor="start" x="566.51" y="-168.5" font-family="Arial" font-size="15.00" fill="#c7d2fe">Resolves shortcut paths to base edge</text>
<text xml:space="preserve" text-anchor="start" x="655.72" y="-150.5" font-family="Arial" font-size="15.00" fill="#c7d2fe">sequences</text>
</g>
<!-- shortcutgraph -->
<g id="node8" class="node">
<title>shortcutgraph</title>
<polygon fill="#6366f1" stroke="#4f46e5" stroke-width="0" points="1282.02,-268 961.98,-268 961.98,-88 1282.02,-88 1282.02,-268"/>
<text xml:space="preserve" text-anchor="start" x="1058.64" y="-192" font-family="Arial" font-size="20.00" fill="#eef2ff">shortcutGraph</text>
<text xml:space="preserve" text-anchor="start" x="983.6" y="-168.5" font-family="Arial" font-size="15.00" fill="#c7d2fe">Graph with adjacency lists, shortcuts, and</text>
<text xml:space="preserve" text-anchor="start" x="1071.96" y="-150.5" font-family="Arial" font-size="15.00" fill="#c7d2fe">edge metadata</text>
</g>
<!-- streamlitui -->
<g id="node9" class="node">
<title>streamlitui</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="590.98,-1534 259.02,-1534 259.02,-1354 590.98,-1354 590.98,-1534"/>
<text xml:space="preserve" text-anchor="start" x="372.77" y="-1467.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Streamlit UI</text>
<text xml:space="preserve" text-anchor="start" x="373.7" y="-1446.1" font-family="Arial" font-size="13.00" fill="#bfdbfe">Python / Streamlit</text>
<text xml:space="preserve" text-anchor="start" x="279.07" y="-1424.7" font-family="Arial" font-size="15.00" fill="#bfdbfe">Interactive map visualization and debugging</text>
<text xml:space="preserve" text-anchor="start" x="396.23" y="-1406.7" font-family="Arial" font-size="15.00" fill="#bfdbfe">interface</text>
</g>
<!-- developer -->
<g id="node10" class="node">
<title>developer</title>
<polygon fill="#a35829" stroke="#7e451d" stroke-width="0" points="595.95,-1866 254.05,-1866 254.05,-1686 595.95,-1686 595.95,-1866"/>
<text xml:space="preserve" text-anchor="start" x="379.42" y="-1790" font-family="Arial" font-size="20.00" fill="#ffe0c2">Developer</text>
<text xml:space="preserve" text-anchor="start" x="274.1" y="-1766.5" font-family="Arial" font-size="15.00" fill="#f9b27c">Uses Streamlit UI for testing and Python SDK</text>
<text xml:space="preserve" text-anchor="start" x="379.14" y="-1748.5" font-family="Arial" font-size="15.00" fill="#f9b27c">for integration</text>
</g>
<!-- routehandler&#45;&gt;datasetregistry -->
<g id="edge3" class="edge">
<title>routehandler&#45;&gt;datasetregistry</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M380.92,-1043.87C360.33,-1002.32 335.75,-952.73 314.62,-910.1"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="317.05,-909.1 311.37,-903.54 312.35,-911.43 317.05,-909.1"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="350.27,-961 350.27,-983.8 426.3,-983.8 426.3,-961 350.27,-961"/>
<text xml:space="preserve" text-anchor="start" x="353.27" y="-968.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">Loads from</text>
</g>
<!-- routehandler&#45;&gt;coordtranslator -->
<g id="edge4" class="edge">
<title>routehandler&#45;&gt;coordtranslator</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M505.12,-1043.87C543.02,-1001.8 588.34,-951.48 627.07,-908.49"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="628.88,-910.41 631.95,-903.08 624.98,-906.89 628.88,-910.41"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="578.17,-961 578.17,-983.8 616.06,-983.8 616.06,-961 578.17,-961"/>
<text xml:space="preserve" text-anchor="start" x="581.17" y="-968.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">Uses</text>
</g>
<!-- coordtranslator&#45;&gt;queryalgorithms -->
<g id="edge5" class="edge">
<title>coordtranslator&#45;&gt;queryalgorithms</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M703.12,-681C702.59,-674.8 702.07,-668.55 701.54,-662.28"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="704.17,-662.27 700.93,-655.02 698.94,-662.71 704.17,-662.27"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="536.35,-666.39 536.35,-689.19 701.89,-689.19 701.89,-666.39 536.35,-666.39"/>
<text xml:space="preserve" text-anchor="start" x="539.35" y="-673.59" font-family="Arial" font-size="14.00" fill="#c9c9c9">Route queries (port 8082)</text>
</g>
<!-- queryalgorithms&#45;&gt;csrgraph -->
<g id="edge6" class="edge">
<title>queryalgorithms&#45;&gt;csrgraph</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M567.96,-410.87C510.47,-368.27 441.58,-317.23 383.08,-273.89"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="384.92,-271.99 377.33,-269.63 381.79,-276.21 384.92,-271.99"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="484.48,-328 484.48,-350.8 539.5,-350.8 539.5,-328 484.48,-328"/>
<text xml:space="preserve" text-anchor="start" x="487.48" y="-335.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">Queries</text>
</g>
<!-- queryalgorithms&#45;&gt;pathexpander -->
<g id="edge7" class="edge">
<title>queryalgorithms&#45;&gt;pathexpander</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M681.62,-411.08C680.42,-384.38 679.82,-355 680.83,-328 681.43,-311.9 682.4,-294.84 683.52,-278.24"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="686.12,-278.65 684.02,-270.99 680.88,-278.29 686.12,-278.65"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="680.83,-328 680.83,-350.8 802,-350.8 802,-328 680.83,-328"/>
<text xml:space="preserve" text-anchor="start" x="683.83" y="-335.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">Expands shortcuts</text>
</g>
<!-- queryalgorithms&#45;&gt;shortcutgraph -->
<g id="edge8" class="edge">
<title>queryalgorithms&#45;&gt;shortcutgraph</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M808.32,-410.87C865.94,-368.27 934.99,-317.23 993.62,-273.89"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="994.92,-276.2 999.39,-269.63 991.8,-271.98 994.92,-276.2"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="918.01,-328 918.01,-350.8 973.03,-350.8 973.03,-328 918.01,-328"/>
<text xml:space="preserve" text-anchor="start" x="921.01" y="-335.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">Queries</text>
</g>
<!-- spatialindex&#45;&gt;shortcutgraph -->
<g id="edge9" class="edge">
<title>spatialindex&#45;&gt;shortcutgraph</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1120.55,-410.87C1120.81,-369.67 1121.12,-320.56 1121.38,-278.17"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1124.01,-278.37 1121.43,-270.86 1118.76,-278.34 1124.01,-278.37"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1121.06,-328 1121.06,-350.8 1218.13,-350.8 1218.13,-328 1121.06,-328"/>
<text xml:space="preserve" text-anchor="start" x="1124.06" y="-335.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">Indexes edges</text>
</g>
<!-- streamlitui&#45;&gt;routehandler -->
<g id="edge2" class="edge">
<title>streamlitui&#45;&gt;routehandler</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M425,-1354.27C425,-1335.69 425,-1315.56 425,-1295.28"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="427.63,-1295.53 425,-1288.03 422.38,-1295.53 427.63,-1295.53"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="324.86,-1319.36 324.86,-1342.16 425,-1342.16 425,-1319.36 324.86,-1319.36"/>
<text xml:space="preserve" text-anchor="start" x="327.86" y="-1326.56" font-family="Arial" font-size="14.00" fill="#c9c9c9">HTTP requests</text>
</g>
<!-- developer&#45;&gt;streamlitui -->
<g id="edge1" class="edge">
<title>developer&#45;&gt;streamlitui</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M425,-1686.13C425,-1642.3 425,-1589.28 425,-1544.14"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="427.63,-1544.27 425,-1536.77 422.38,-1544.27 427.63,-1544.27"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="425,-1603.2 425,-1626 563.28,-1626 563.28,-1603.2 425,-1603.2"/>
<text xml:space="preserve" text-anchor="start" x="428" y="-1610.4" font-family="Arial" font-size="14.00" fill="#c9c9c9">Uses for visualization</text>
</g>
</g>
</svg>
`;default:throw new Error("Unknown viewId: "+e)}}export{t as dotSource,n as svgSource};
