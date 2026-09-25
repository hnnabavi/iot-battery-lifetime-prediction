"""Component-level external rate-shape check against Ravikumar et al. (2025)."""
import numpy as np

currents = np.array([1.0,10.0,30.0,100.0])
model = np.clip((1.0/currents)**(1.10-1.0),0.50,1.15)
measured = {
    "EVE": np.array([3.78,2.94,2.17,0.61]),
    "Saft": np.array([4.08,2.85,1.81,0.58]),
}

for brand, energy in measured.items():
    observed = energy / energy[0]
    print(brand)
    for current,pred,obs in zip(currents,model,observed):
        err=100.0*(pred-obs)/obs
        print(f"  {current:>5.0f} mA: model={pred:.3f}, observed={obs:.3f}, error={err:+.1f}%")
