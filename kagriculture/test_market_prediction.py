import pytest
from market_model import MarketTracker, get_exact_price

def test_get_exact_price():
    # Test WHEAT pricing at various inventories based on our previous observations
    # Step 0: WHEAT: Price=25, Inventory=10000
    assert get_exact_price("WHEAT", 10000) == 25
    
    # Step 1: WHEAT: Price=32, Inventory=9949
    assert get_exact_price("WHEAT", 9949) == 32
    
    # Step 49: MILK: Price=175, Inventory=9997
    assert get_exact_price("MILK", 9997) == 175
    
    # Step 49: WOOL: Price=212, Inventory=9997
    assert get_exact_price("WOOL", 9997) == 212
    
    print("All assertions passed!")

if __name__ == "__main__":
    test_get_exact_price()
