From project guide: The UAV is a "1:1 scale" vehicle of itself. Froude and Mach numbers are physically consistent. Reynolds number is higher than wind tunnel models of the same size (due to higher speed).
Question: Can we test scaled down versions of wings?

From project guide: "Disposable" UAVs (like X-56A) allow for testing past the flutter
point.
Question: Do we need to test to failure? Imposes severe limits on the feasible design configurations.

From project guide: Atmospheric turbulence can be used to excite flutter, but it is random and not sufficient to excite all modes of interest. 
A basic frequency sweep (slowly stepping through one frequency at a time) works but takes a long time.
Instead, orthogonal phase-optimised multisines, where a deterministic signal composed of a sum of sinusoids at specific frequencies of interest is used. 
Note: Crest factor measures the accumulated "peakiness" of the different sinusoids, you want it low. Also, since the signals are orthogonal, you can later decouple them and figure out which response came from which surface.
Inertial shakers can also be used to induce local excitation, especially useful for modes that are difficult to excite with control surfaces.

Question: If we decide to use shakers, do we need to design for them, e.g. say how they will be integrated in the structure?