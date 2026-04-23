import os,sys,twtnamelist,folium,geopandas,branca,numpy,rasterio,rasterio.warp,rasterio.io
import math
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling, transform_bounds
from rasterio.transform import array_bounds

class twtfoliummap(folium.Map):

    def __init__(self,nl:twtnamelist.Namelist,*args,**kwargs):
        super().__init__(*args, **kwargs)
        self._set_fnames(nl=nl)
        self._add_domain(nl=nl)
        self._add_nhd()

    def _set_fnames(self,nl:twtnamelist.Namelist):
        """Set file names for various data layers"""
        dstr                      = (nl.time.datetime_dim[0].strftime('%Y%m%d')+'_to_'+
                                     nl.time.datetime_dim[len(nl.time.datetime_dim)-1].strftime('%Y%m%d'))
        dinput                    = nl.dirnames.input
        doutput                   = nl.dirnames.output_summary
        self.fname_soil_texture   = nl.fnames.soil_texture
        self.fname_transmissivity = nl.fnames.soil_transmissivity
        self.fname_nhd            = nl.fnames.nhdp
        self.fname_twi            = nl.fnames.twi
        self.fname_slope          = nl.fnames.slope
        self.fname_flow_acc       = nl.fnames.facc_sca
        self.fname_dem            = nl.fnames.dem      
        self.fname_dem_breached   = nl.fnames.dem_breached 
        self.fname_percinundated  = os.path.join(doutput,"".join(['percent_inundated_grid_',dstr,'.tiff']))
        self.fname_meanwtd        = os.path.join(doutput,"".join(['mean_wtd_',dstr,'.tiff']))
        self.fname_nonperennial   = os.path.join(doutput,"".join(['nonperennial_strms_',dstr,'.tiff']))
        self.fname_perennial      = os.path.join(doutput,"".join(['perennial_strms_',dstr,'.tiff']))

    def add_transmissivity(self):
        """Add transmissivity data to self"""
        if not os.path.isfile(self.fname_transmissivity): 
            sys.exit('ERROR _add_transmissivity could not find '+self.fname_transmissivity)
        self._add_grid(name='Transmissivity Decay Factor (f)',
                      fname=self.fname_transmissivity,
                      cmap=branca.colormap.linear.viridis)

    def add_twi(self):
        """Add topological wetness index (TWI) data to self"""
        if not os.path.isfile(self.fname_twi): 
            sys.exit('ERROR add_twi could not find '+self.fname_twi)
        self._add_grid(name='Topological Wetness Index (TWI)',
                      fname=self.fname_twi,
                      cmap=branca.colormap.linear.viridis)

    def add_slope(self):
        """Add slope data to self"""
        if not os.path.isfile(self.fname_slope): 
            sys.exit('ERROR add_slope could not find '+self.fname_slope)
        self._add_grid(name='Slope (degrees)',
                      fname=self.fname_slope,
                      cmap=branca.colormap.linear.Greys_07)

    def add_facc(self):
        """Add flow accumulation data to self"""
        if not os.path.isfile(self.fname_flow_acc): 
            sys.exit('ERROR add_facc could not find '+self.fname_flow_acc)
        self._add_grid(name='Flow accumulation',
                      fname=self.fname_flow_acc,
                      cmap=branca.colormap.linear.viridis)

    def add_dem(self):
        """Add dems to self"""
        if not os.path.isfile(self.fname_dem):          
            sys.exit('ERROR get_fmap_dem could not find '+self.fname_dem)
        self._add_grid(name='DEM (m)',
                      fname=self.fname_dem,
                      cmap=branca.colormap.linear.Greys_07)
        #if not os.path.isfile(self.fname_dem_breached): 
        #    sys.exit('ERROR get_fmap_dem could not find '+self.fname_dem_breached)
        #self._add_grid(name='DEM (breached) (m)',
        #              fname=self.fname_dem_breached,
        #              cmap=branca.colormap.linear.Greys_07)

    def add_meanwtd(self,namelist:twtnamelist.Namelist):
        """Add mean wtd data to self"""
        fname = self.fname_meanwtd
        if not os.path.isfile(fname): 
            sys.exit(f'ERROR add_meanwtd could not find {fname}')
        cmap = branca.colormap.linear.viridis
        self._add_grid(name= f'Mean WTD (m) ({namelist.options.name_resample_method})',
                       fname=os.path.join(dir,fname),
                       cmap = cmap)

    def add_percinundated(self,namelist:twtnamelist.Namelist,fname:str=None):
        """Get folium map of mean percent inundation values for full grid"""
        if fname is None: fname = self.fname_percinundated
        if not os.path.isfile(fname): 
            sys.exit(f'ERROR add_percinundated could not find {fname}')
        cmap = branca.colormap.linear.Reds_08
        self._add_grid(name=f'WTD-TWI %-Inundated ({namelist.options.name_resample_method})',
                       fname=fname,
                       cmap=cmap)

    def add_nonperennial_strm_classification(self,fname:str=None):
        """Add non-perennial stream classification to self"""
        if fname is None: fname = self.fname_nonperennial
        if not os.path.isfile(fname): 
            sys.exit(f'ERROR add_nonperennial_strm_classification could not find {fname}')
        cmap = branca.colormap.linear.Blues_07
        self._add_grid(name=f'WTD-TWI Non-perennial',
                        fname=fname,
                        cmap=cmap)
                
    def add_perennial_strm_classification(self,fname:str=None):
        """Get folium map of mean WTD values"""
        if fname is None: fname = self.fname_perennial
        if not os.path.isfile(fname): 
            sys.exit(f'ERROR add_perennial_strm_classification could not find {fname}')
        cmap = {1: "#ff0000"}
        if os.path.isfile(fname):
            self._add_grid(name=f'WTD-TWI Perennial',
                            fname=fname,
                            cmap=cmap)
        html_legend = """
        <div style="position: fixed; 
        bottom: 10px; left: 10px; width: 150px; height: auto; 
        border:2px solid grey; z-index:9999; font-size:14px;
        background-color:white; opacity: 0.85; padding: 10px;">
        """
        html_legend += f'<div style="display: flex; align-items: center; margin-bottom: 5px;"><div style="width: 20px; height: 20px; background-color: {cmap[1]}; margin-right: 5px;"></div>{'Perennial'}</div>'
        html_legend += "</div>"
        self.get_root().html.add_child(folium.Element(html_legend))
        #&nbsp; <b>WTD-TWI Classification</b> <br>

    def _add_grid(self, name: str, fname: str, cmap: "branca.colormap.ColorMap | dict"):
        """Add gridded data to a Folium map as a palettized PNG data-URI.
        
        - NaNs are transparent (palette index 0).
        - Continuous case (vmin != vmax) uses the provided ColorMap (branca) for the palette and adds a legend.
        - Binary/degenerate case (all finite pixels have the same value, e.g., 1/NaN) maps all finite pixels to a single color
        and adds a simple legend.
        
        Args:
            name: Layer/legend name.
            fname: Path to a single-band GeoTIFF.
            cmap: Either a branca ColorMap (for continuous data) or a dict for the binary case, e.g., {1: "#1f78b4"}.
        """
        import os, sys, math, io, base64, re
        import numpy as np
        import folium
        import branca
        import rasterio
        from rasterio.warp import calculate_default_transform, reproject, Resampling, transform_bounds
        from rasterio.transform import array_bounds
        from PIL import Image

        if not os.path.isfile(fname):
            sys.exit(f'ERROR _add_grid could not find {fname}')
        if not (fname.endswith('.tif') or fname.endswith('.tiff')):
            sys.exit('ERROR _add_grid fname does not end in .tif ' + fname)

        def _hex_to_rgb(h: str):
            s = h.lstrip('#')
            if len(s) in (3, 4):  # short hex like #abc or #rgba
                s = ''.join(ch * 2 for ch in s[:3])
            return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))

        def _parse_color_to_rgb(c):
            # Accept '#RRGGBB', '#RRGGBBAA', 'rgb(r,g,b)', 'rgba(r,g,b,a)', or tuples/lists
            if isinstance(c, str):
                c = c.strip()
                if c.startswith('#'):
                    return _hex_to_rgb(c)
                m = re.match(r'rgba?\(\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)', c)
                if m:
                    r, g, b = m.groups()
                    # Values may be 0-255 or 0-1 floats; cast safely to 0-255
                    vals = [float(r), float(g), float(b)]
                    if max(vals) <= 1.0:
                        vals = [int(round(v * 255)) for v in vals]
                    else:
                        vals = [int(round(v)) for v in vals]
                    return tuple(np.clip(vals, 0, 255).astype(int).tolist())
                # Fallback: try hex without '#'
                try:
                    return _hex_to_rgb('#' + c)
                except Exception:
                    return (31, 120, 180)  # default
            if isinstance(c, (tuple, list)) and len(c) >= 3:
                vals = list(c[:3])
                # If floats 0-1, scale; if ints 0-255, keep
                if any(isinstance(v, float) for v in vals) and max(vals) <= 1.0:
                    vals = [int(round(v * 255)) for v in vals]
                vals = [int(round(v)) for v in vals]
                return tuple(np.clip(vals, 0, 255).astype(int).tolist())
            return (31, 120, 180)

        folium_crs = "EPSG:3857"
        with rasterio.open(fname, 'r') as src:
            # Compute target grid in Web Mercator
            dst_transform, dst_width, dst_height = calculate_default_transform(
                src.crs, folium_crs, src.width, src.height, *src.bounds
            )

            # Reproject into a float32 array with NaN as nodata
            vals = np.full((dst_height, dst_width), np.nan, dtype=np.float32)
            reproject(
                source=rasterio.band(src, 1),
                destination=vals,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=dst_transform,
                dst_crs=folium_crs,
                resampling=Resampling.nearest,
                src_nodata=src.nodata,
                dst_nodata=np.nan,
            )

            # Bounds in lat/lon for Leaflet
            bounds_merc = array_bounds(dst_height, dst_width, dst_transform)
            bbox = transform_bounds(folium_crs, "EPSG:4326", *bounds_merc)

            # Compute vmin/vmax ignoring NaNs
            finite_mask = np.isfinite(vals)
            if finite_mask.any():
                vmin = float(vals[finite_mask].min())
                vmax = float(vals[finite_mask].max())
            else:
                vmin, vmax = 0.0, 1.0  # degenerate: all NaN

            # Prepare and add legend (Branca colorbar) if applicable (continuous only)
            cm_for_palette = None
            if isinstance(cmap, branca.colormap.ColorMap) and vmin != vmax and math.isfinite(vmin) and math.isfinite(vmax):
                cm_for_palette = cmap.scale(vmin, vmax)
                cm_for_palette.caption = name
                cm_for_palette.add_to(self)

            # Build a 256-color palette:
            # - index 0 is reserved for NaN (transparent)
            # - indices 1..255 span vmin..vmax (or a single color in binary/degenerate case)
            palette = np.zeros((256, 3), dtype=np.uint8)
            if cm_for_palette is not None:
                sample_vals = np.linspace(vmin, vmax, 255, dtype=np.float32)
                for i, v in enumerate(sample_vals, start=1):
                    palette[i] = _parse_color_to_rgb(cm_for_palette(float(v)))
            else:
                # Fallback palette: grayscale for indices 1..255; may be overridden in degenerate case below
                palette[1:, 0] = np.arange(1, 256, dtype=np.uint8)
                palette[1:, 1] = np.arange(1, 256, dtype=np.uint8)
                palette[1:, 2] = np.arange(1, 256, dtype=np.uint8)

            # Map vals -> palette indices
            idx = np.zeros(vals.shape, dtype=np.uint8)  # default 0 for NaN (transparent)
            if finite_mask.any() and vmin != vmax and math.isfinite(vmin) and math.isfinite(vmax):
                norm = np.clip((vals[finite_mask] - vmin) / (vmax - vmin), 0.0, 1.0)
                idx_vals = 1 + (norm * 254.0).astype(np.uint8)  # 1..255
                idx[finite_mask] = idx_vals
            elif finite_mask.any():
                # Degenerate range: all finite values are equal (e.g., 1). Map them to a visible index (255).
                idx[finite_mask] = 255

                # Choose the single inundation color for palette[255]
                chosen_rgb = (31, 120, 180)  # default #1f78b4
                if isinstance(cmap, dict):
                    # Try explicit mapping for value 1, then vmin as float/int, else default
                    color_spec = cmap.get(1, cmap.get(float(vmin), cmap.get(int(vmin), "#1f78b4")))
                    chosen_rgb = _parse_color_to_rgb(color_spec)
                elif isinstance(cmap, branca.colormap.ColorMap):
                    # Sample a single color (at vmin or mid)
                    try:
                        color_spec = cmap(float(vmin))
                    except Exception:
                        color_spec = cmap(0.5) if hasattr(cmap, "__call__") else "#1f78b4"
                    chosen_rgb = _parse_color_to_rgb(color_spec)
                palette[255] = chosen_rgb

            # NaNs remain 0 (transparent)

            # Create a palettized PIL image (mode 'P') with transparency at index 0
            img = Image.fromarray(idx, mode='P')
            img.putpalette(palette.reshape(-1).tolist())
            img.info['transparency'] = 0  # palette index 0 transparent

            # Convert to a PNG data-URI string so Folium can serialize it
            buf = io.BytesIO()
            img.save(buf, format='PNG', optimize=True)
            data_uri = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('ascii')

            # Pass the data-URI to Folium (no colormap argument)
            overlay = folium.raster_layers.ImageOverlay(
                name=name,
                image=data_uri,
                bounds=[[bbox[1], bbox[0]], [bbox[3], bbox[2]]],
                opacity=1.0,
                interactive=False,
                cross_origin=False,
            )
            overlay.add_to(self)
            return overlay
            
    def _add_vector(self,name:str,fname:str,name_in_file:str,cmap:branca.colormap.ColorMap|dict):
        """Add vector data to map"""
        if not os.path.isfile(fname): 
            sys.exit('ERROR _add_vector could not find '+fname)
        if fname.find('.gpkg') != -1 or fname.find('.shp') != -1: 
            sys.exit('ERROR _add_vector fname does not end in .shp or .gpkg '+fname) 
        shp = geopandas.read_file(fname)
        shpfg = folium.FeatureGroup(name=name)
        if isinstance(cmap, dict):
            for _, r in shp.iterrows():
                folium.PolyLine(
                    locations=[(lat, lon) for lon, lat in r.geometry.coords],
                    color=cmap[r[name_in_file]]
                ).add_to(shpfg)
        if isinstance(cmap, branca.colormap.ColorMap):
            for _, r in shp.iterrows():
                folium.PolyLine(
                    locations=[(lat, lon) for lon, lat in r.geometry.coords],
                    color=cmap(r[name_in_file])
                ).add_to(shpfg)
        shpfg.add_to(self)

    def add_texture(self):
        """Add soil texture data to self"""
        fname = self.fname_soil_texture
        if not os.path.isfile(fname): 
            sys.exit(f'ERROR add_texture could not find {fname}')
        soils = geopandas.read_file(fname)
        textures = sorted(set(soils['texture']))
        cmap = branca.colormap.linear.viridis.scale(0, len(textures)).to_step(len(textures))
        texture_colors = {texture: cmap(i) for i, texture in enumerate(textures)}
        soilsfg = folium.FeatureGroup(name='Soil texture')
        for texture, texture_group in soils.groupby('texture'):
            for index, row in texture_group.iterrows():
                folium.GeoJson(
                    data=geopandas.GeoSeries(row['geometry']).to_json(),
                    style_function=lambda x, 
                    color=texture_colors[texture]: {"fillColor": color, 
                                                    "color": "black", 
                                                    "fillOpacity": 1.0}
                ).add_to(soilsfg)
        soilsfg.add_to(self)
        html_legend = """
        <div style="position: fixed; 
        top: 10px; left: 60px; width: 200px; height: auto; 
        border:2px solid grey; z-index:9999; font-size:14px;
        background-color:white; opacity: 0.85; padding: 10px;">
        <b>Soil Texture</b><br>
        """
        for texture, color in texture_colors.items():
            html_legend += f'<div style="display: flex; align-items: center; margin-bottom: 5px;"><div style="width: 20px; height: 20px; background-color: {color}; margin-right: 5px;"></div>{texture}</div>'
        html_legend += "</div>"
        self.get_root().html.add_child(folium.Element(html_legend))

    def _add_domain(self,nl:twtnamelist.Namelist):
        """Add domain boundary to self"""
        if not os.path.isfile(nl.fnames.domain): 
            sys.exit('ERROR _add_domain could not find '+nl.fnames.domain)
        domain = geopandas.read_file(nl.fnames.domain)
        domainfg = folium.FeatureGroup(name='Domain')
        for _, r in domain.iterrows():
            folium.GeoJson(data=geopandas.GeoSeries(r['geometry']).to_json(),
                           style_function=lambda x:{"color":"black","fillColor":"none"}).add_to(domainfg)
        domainfg.add_to(self)
        domain_centroid = domain.to_crs('+proj=cea').centroid.to_crs(domain.crs)
        self.location = [domain_centroid.y.iloc[0], domain_centroid.x.iloc[0]]
        self.fit_bounds([[domain.bounds.miny.iloc[0], domain.bounds.minx.iloc[0]],
                      [domain.bounds.maxy.iloc[0], domain.bounds.maxx.iloc[0]]])
        
    def _add_boundary(self,fname_boundary:str):
        """Add boundary to self"""
        if not os.path.isfile(fname_boundary): 
            sys.exit('ERROR _add_boundary could not find '+fname_boundary)
        boundary = geopandas.read_file(fname_boundary)
        folium_crs = "EPSG:4326"
        boundary = boundary.to_crs(folium_crs)
        boundaryfg = folium.FeatureGroup(name='Boundary')
        for _, r in boundary.iterrows():
            folium.GeoJson(data=geopandas.GeoSeries(r['geometry']).to_json(),
                           style_function=lambda x:{"color":"black","fillColor":"none"}).add_to(boundaryfg)
        boundaryfg.add_to(self)
        boundary_centroid = boundary.to_crs('+proj=cea').centroid.to_crs(boundary.crs)
        self.location = [boundary_centroid.y.iloc[0], boundary_centroid.x.iloc[0]]
        self.fit_bounds([[boundary.bounds.miny.iloc[0], boundary.bounds.minx.iloc[0]],
                      [boundary.bounds.maxy.iloc[0], boundary.bounds.maxx.iloc[0]]])

    def _add_nhd(self):
        """Add nhd boundary to self"""
        fname = self.fname_nhd
        if not os.path.isfile(fname): 
            sys.exit('ERROR _add_nhd could not find '+fname)
        nhd = geopandas.read_file(fname)
        nhdfg = folium.FeatureGroup(name='NHD HD')
        for _, r in nhd.iterrows(): 
            folium.GeoJson(data=geopandas.GeoSeries(r['geometry']).to_json()).add_to(nhdfg)
        nhdfg.add_to(self)
