# faraday.py
# Models hydrogen production using Faraday's Law of Electrolysis
# This is the core production equation, as everything else feeds into this. 

from config import FARADAY_CONSTANT, ELECTRONS_PER_H2, MOLAR_VOLUME

def calculate_moles_h2(current, time_seconds):
    """
    Calculate moles of hydrogen produced. 

    current     : operating current in Amps (A)
    time_seconds    : duration of operation in seconds (s)
    returns     : moles of H2 produced (mol)
    """
    charge = current * time_seconds
    moles = charge / (ELECTRONS_PER_H2 * FARADAY_CONSTANT)
    return moles

def calculate_liters_h2(current, time_seconds): 
    """
    Calculate volume of hydrogen produced at STP. \
    current     : operating current in Amps (A)
    time_seconds    : duration of operation in seconds(s)
    returns     : volume of H2 in liters (L)
    """
    moles = calculate_moles_h2(current, time_seconds)
    liters = moles * MOLAR_VOLUME
    return liters

def calculate_production_rate(current): 
    """
    Calculate hydrogen production rate per hour. 

    current     : operating current in Amps (A)
    returns     : litiers of H2 per hour (L/hr)
    """
    liters_per_hour = calculate_liters_h2(current, 3600)
    return liters_per_hour

if __name__=="__main__":
    rate = calculate_production_rate(1.0)
    print(f"At 1A, production rate: {rate: .4f} L/hr")
    print(f"Expected: ~0.4185 L/hr")