# Sim/Spy memory readback test.
from tdf.mp7.images import AlgoBxMemoryImage

ITEM = "gt_mp7_gtlfdl.algo_bx_mem"
image = AlgoBxMemoryImage()

image.fill_random()
blockwrite(TDF_DEVICE, ITEM, image.serialize(), verify = True)

image.fill_counter()
blockwrite(TDF_DEVICE, ITEM, image.serialize(), verify = True)

image.clear()
blockwrite(TDF_DEVICE, ITEM, image.serialize(), verify = True)
