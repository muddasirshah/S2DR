var naip_image_collection_hr = ee.ImageCollection("USDA/NAIP/DOQQ")
        .filter(ee.Filter.bounds(geometry2.centroid(0.1)))
        .filter(ee.Filter.date('2015-01-01','2025-11-16'))

var block = '20';   
Map.centerObject(geometry2, 13);

var geometry_cm = geometry2
var sd = ee.Date('2015-01-01');
var ed =  ee.Date('2025-11-16'); 
    
    // link collections
    function linkCols(aoi, start_date, end_date){
        var s2_sr_col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(geometry_cm).filterDate(start_date, end_date)).filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE',10))
        var s2_cloudless_col = (ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY').filterBounds(geometry_cm).filterDate(start_date, end_date))
        return ee.ImageCollection(ee.Join.saveFirst('s2cloudless').apply({'primary': s2_sr_col,'secondary': s2_cloudless_col, 'condition': ee.Filter.equals({'leftField': 'system:index','rightField': 'system:index'})}))
    }
    var s2_filtered = linkCols(geometry_cm, sd, ed)

// print(s2_filtered)
    // Adding Probability as "cloud" band
    function add_cloud_bands(img){
        var cld_prb = ee.Image(img.get('s2cloudless')).select('probability')
        var is_cloud = cld_prb.gt(CLD_PRB_THRESH).rename('clouds')
        return img.addBands(ee.Image([cld_prb, is_cloud]))
    }
    // CLOUD COMPONENTS
    var CLD_PRB_THRESH = 50 //very sensitive to haze, might mask waterbodies with strict threshold i.e. lt 5
    var NIR_DRK_THRESH = 0.15 //0.15 () // sensitive to thresholds greater than 0.18
    var CLD_PRJ_DIST = 1
    var BUFFER = 50
    
    // SHADOW COMPONENTS
    function add_shadow_bands(img){
        var not_water = img.select('SCL').neq(6)
        var SR_BAND_SCALE = 1e4
        var dark_pixels = img.select('B8').lt(NIR_DRK_THRESH*SR_BAND_SCALE).multiply(not_water).rename('dark_pixels')
        // Determine the direction to project cloud shadow from clouds (assumes UTM projection).
        var shadow_azimuth = ee.Number(90).subtract(ee.Number(img.get('MEAN_SOLAR_AZIMUTH_ANGLE')));
        // Project shadows from clouds for the distance specified by the CLD_PRJ_DIST input.
        var cld_proj = (img.select('clouds').directionalDistanceTransform(shadow_azimuth, CLD_PRJ_DIST*10)
            .reproject({'crs': img.select(0).projection(), 'scale': 100})
            .select('distance')
            .mask()
            .rename('cloud_transform'))
        // Identify the intersection of dark pixels with cloud shadow projection.
        var shadows = cld_proj.multiply(dark_pixels).rename('shadows')
        // Add dark pixels, cloud projection, and identified shadows as image bands.
        return img.addBands(ee.Image([dark_pixels, cld_proj, shadows]))
    }
    
    function add_cld_shdw_mask(img){
        var img_cloud = add_cloud_bands(img)
        var img_cloud_shadow = add_shadow_bands(img_cloud)
    
        // Combine cloud and shadow mask, set cloud and shadow as value 1, else 0.
        var is_cld_shdw = img_cloud_shadow.select('clouds').add(img_cloud_shadow.select('shadows')).gt(0)
    
        // Remove small cloud-shadow patches and dilate remaining pixels by BUFFER input.
        // 20 m scale is for speed, and assumes clouds don't require 10 m precision.
        var is_cld_shdw2 = (is_cld_shdw.focal_min(2).focal_max(BUFFER*2/20)
            .reproject({'crs': img.select([0]).projection(), 'scale': 20})
            .rename('cloudmask'))
    
        // Add the final cloud-shadow mask to the image.
        return img_cloud_shadow.addBands(is_cld_shdw2)
    }
    
    
    function apply_cld_shdw_mask(img) {
        // # Subset the cloudmask band and invert it so clouds/shadow are 0, else 1.
        var not_cld_shdw = img.select('cloudmask').not()
    
        // # Subset reflectance bands and update their masks, return the result.
        return img.select('B.*').updateMask(not_cld_shdw)
    }
    
    
    // Display all of the cloud and cloud shadow components
    // The input is an image collection where each image is the result of the add_cld_shdw_mask function
    var s2_filtered = s2_filtered.map(add_cld_shdw_mask)
    
    
    // // Add the combined masks as a band
    var s2_filtered = s2_filtered.map(function(img){
        var clouds = img.select('clouds')
        var shadows = img.select('shadows')
        var darkPixels = img.select('dark_pixels')
        var combined = (clouds.add(shadows).add(darkPixels)).gt(0).not().selfMask().rename('cloudmask');
        var prob = img.select('probability');
        return img.select('B.*').updateMask(combined).multiply(0.0001).addBands([combined,prob]).copyProperties(img,['system:time_start']);
    })
    
  var s2 = s2_filtered;      


        
//Cloud Masking End 
// Define the date range in while the images has to be searched. 
var days = 1

var millis = ee.Number(days).multiply(1000*60*60*24)

var maxDiffFilter = ee.Filter.maxDifference({
  difference: millis,
  leftField: 'system:time_start',
  rightField: 'system:time_start'
})

// Define a geom filter to find images that match spatially
var geomFilter = ee.Filter.intersects({
  leftField:'.geo',
  rightField:'.geo',
  maxError:0.1
})

var filter = ee.Filter.and(maxDiffFilter, geomFilter)

var join = ee.Join.saveAll({
  matchesKey: 'matches', 
  ordering: 'system:time_start',
  ascending: false})
  
var joinResult = join.apply({
  primary: s2,
  secondary: naip_image_collection_hr,
  condition: filter
})

// Check the join results
var s2Image = ee.Image(joinResult.first())
var s1Image = ee.Image(ee.ImageCollection.fromImages(s2Image.get('matches')).mosaic())

// You will have 0 or more matches of overlapping S1 images
// for each S2 image
// We want to retain only the overlapping regions
// map() a function and create a multiband image with S2 and S1 bands
// mask areas where images do not overlap
var joinProcessed = ee.ImageCollection(joinResult.map(function(image) {
  var s2Image = ee.Image(image)
  var s1Image = ee.Image(ee.ImageCollection.fromImages(image.get('matches')).mosaic())
  var s1Mask = s1Image.mask().select(0)
  var s2Mask = s2Image.mask().select(0)
  var overlapImage = ee.Image.cat([s2Image, s1Image])
  return overlapImage.updateMask(s1Mask).updateMask(s2Mask)
}))

print(joinProcessed,'Sentinel-2 Image Collection with RVI of the matching date')



var dates = joinProcessed.map(function(img){
  var date = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd')
  return ee.Feature(null,{'date':date})
})

print(dates.aggregate_array('date'))
var dates = dates.limit(1).aggregate_array('date').distinct()

dates.evaluate(function(dates){
  var dates_list = dates;
  for(var date in dates_list){
    var day = dates_list[date]
    var start = ee.Date(day)
    var end = start.advance({delta:1,unit:'day'})
    var image = joinProcessed.filterDate(start,end).first()

    var naip_image = image.select(['B', 'G', 'R']).unmask(-9999).double(); 
    var naip_image_resampled = naip_image.clip(geometry2).reproject({
      crs: 'EPSG:4326',
      scale: 3 
    });
    var naip_image_visualized = naip_image_resampled.visualize({min:50, max:200, bands:['R','G','B']})
    var naip_image_vis_rn = naip_image_visualized.select(['vis-red','vis-green','vis-blue']).rename(['R','G','B'])
  
  
    var s2_image = image.select(['B2', 'B3', 'B4']).unmask(-9999).double();
    var s2_image_resampled = s2_image.clip(geometry2)
     .reduceResolution({
      reducer: ee.Reducer.mean(),
      maxPixels: 4096
    })
    .reproject({
      crs: naip_image_vis_rn.projection(),
    });
    var s2_image_visualized = s2_image_resampled.visualize({min:0, max:0.20, bands:['B4','B3','B2']})
    var s2_image_vis_rn = s2_image_visualized.select(['vis-red','vis-green','vis-blue']).rename(['R','G','B'])

    Map.addLayer(naip_image_vis_rn,{},'NAIP Image')
    Map.addLayer(s2_image_vis_rn,{},'S2 Image')

    
    var formatOptions = {
      cloudOptimized: true
    }
    
    Export.image.toCloudStorage({
      image: s2_image_vis_rn,
      description: 's2_' + day,
      bucket: 'YOUR_GCP_BUCKET_NAME',
      fileNamePrefix: 'superresolution/'+block+'/msi/' + day + '_msi',
      region: geometry_cm,
      scale: 3, 
      maxPixels:1e13,
      formatOptions:formatOptions,
       skipEmptyTiles:true
    });
    
    Export.image.toCloudStorage({
      image: naip_image_vis_rn,
      description: 'naip_' + day,
      bucket: 'YOUR_GCP_BUCKET_NAME',
      fileNamePrefix: 'superresolution/'+block+'/naip/' + day + '_naip',
      region: geometry_cm,
      scale: 3, 
      maxPixels: 1e13,
      formatOptions:formatOptions,
      skipEmptyTiles:true
    });
         
    
  }
})
