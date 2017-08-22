# Sim/Spy memory readback test.
from tdf.mp7.images import FinorMemoryImage

ITEM = "gt_mp7_frame.spymem2_finor"
image = FinorMemoryImage()

image.fill_random()
blockwrite(TDF_DEVICE, ITEM, image.serialize(), verify=True)

image.fill_counter()
blockwrite(TDF_DEVICE, ITEM, image.serialize(), verify=True)

image.clear()
blockwrite(TDF_DEVICE, ITEM, image.serialize(), verify=True)
