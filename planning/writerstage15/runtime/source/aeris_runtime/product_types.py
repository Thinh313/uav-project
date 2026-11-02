"""Closed exact provider types; no arbitrary app/device selection or subclasses."""
def selected_types(manifest):
 package=manifest['native'].get('package')
 if package=='vn.rtr.aeris.mission':
  from .android import AndroidDevice
  from .product_native import ProductNativeProbe
  return AndroidDevice,ProductNativeProbe
 if package=='vn.rtr.aeris.betasim09':
  from .application09 import AndroidDomain09
  from .product_native09 import ProductNativeProbe09
  return AndroidDomain09,ProductNativeProbe09
 raise ValueError('EXACT_SOURCE_SELECTED_PRODUCT_APPLICATION')
def is_product_probe(probe):
 from .product_native import ProductNativeProbe
 from .product_native09 import ProductNativeProbe09
 return type(probe)in(ProductNativeProbe,ProductNativeProbe09)
def observation_reader(manifest):
 if manifest['native'].get('package')=='vn.rtr.aeris.betasim09':
  from .product_native09 import verify_originals
 elif manifest['native'].get('package')=='vn.rtr.aeris.mission':
  from .product_native import verify_originals
 else:raise ValueError('EXACT_SOURCE_SELECTED_PRODUCT_APPLICATION')
 return verify_originals
