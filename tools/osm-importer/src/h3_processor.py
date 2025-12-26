import h3
from tqdm import tqdm

class H3Processor:
    @staticmethod
    def latlng_to_cell(lat, lng, resolution=15):
        """Convert coordinates to H3 cell."""
        cell_str = h3.latlng_to_cell(lat, lng, resolution)
        return h3.str_to_int(cell_str)
    
    @staticmethod
    def find_lca(cell1, cell2):
        """Find Lowest Common Ancestor between two H3 cells."""
        if cell1 == 0 or cell2 == 0:
            return 0
        
        cell1_res = h3.get_resolution(h3.int_to_str(cell1))
        cell2_res = h3.get_resolution(h3.int_to_str(cell2))
        lca_res = min(cell1_res, cell2_res)
        
        while lca_res >= 0:
            if (h3.cell_to_parent(h3.int_to_str(cell1), lca_res) ==
                h3.cell_to_parent(h3.int_to_str(cell2), lca_res)):
                return h3.str_to_int(h3.cell_to_parent(h3.int_to_str(cell1), lca_res))
            lca_res -= 1
        
        return 0

    @staticmethod
    def get_lca_resolution(cell1, cell2):
        """Get resolution of LCA between two cells."""
        lca = H3Processor.find_lca(cell1, cell2)
        if lca == 0:
            return -1
        return h3.get_resolution(h3.int_to_str(lca))
    
    @staticmethod
    def add_h3_cells(edges_df, nodes_df, resolution=15):
        """Add H3 cells to edges dataframe."""
        tqdm.pandas(desc="Adding H3 cells to edges")
        
        edges_df['to_cell'] = edges_df['target'].progress_apply(
            lambda t: H3Processor.latlng_to_cell(
                nodes_df.loc[t]['geometry'].y,
                nodes_df.loc[t]['geometry'].x,
                resolution
            )
        )
        edges_df['from_cell'] = edges_df['source'].progress_apply(
            lambda s: H3Processor.latlng_to_cell(
                nodes_df.loc[s]['geometry'].y,
                nodes_df.loc[s]['geometry'].x,
                resolution
            )
        )
        
        # Enforce integer type
        edges_df['to_cell'] = edges_df['to_cell'].astype(int)
        edges_df['from_cell'] = edges_df['from_cell'].astype(int)
        
        edges_df['lca_res'] = edges_df.progress_apply(
            lambda row: H3Processor.get_lca_resolution(
                row['to_cell'],
                row['from_cell']
            ),
            axis=1
        )
        return edges_df
