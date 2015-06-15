# Sim memory readback test.
from tdf.mp7.images import SimSpyMemoryImage

ITEM = "tdf_mp7.simspymem"
image = SimSpyMemoryImage()

image.fill_random()
blockwrite(TDF_DEVICE, ITEM, image.serialize(), verify = True)

image.fill_counter()
blockwrite(TDF_DEVICE, ITEM, image.serialize(), verify = True)

image.clear()
blockwrite(TDF_DEVICE, ITEM, image.serialize(), verify = True)
