import inspect
from ib_insync import IB, Contract, Order, util

# Use the util.startLoop() hack just to initialize the IB object safely
# for synchronous inspection if needed, though often unnecessary for simple inspect.
util.startLoop() 
ib = IB()

# 1. Inspecting placeOrder
print("--- Signature for ib.placeOrder ---")
sig_place_order = inspect.signature(ib.placeOrder)
print(sig_place_order) 

# 2. Inspecting reqContractDetails
print("\n--- Signature for ib.reqContractDetailsAsync ---")
sig_req_cd = inspect.signature(ib.reqContractDetailsAsync)
print(sig_req_cd)