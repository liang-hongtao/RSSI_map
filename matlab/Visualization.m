mapFileName = 'FirstFloor.stl';

fc = 5.8e9;
lambda = physconst("lightspeed")/fc;
txArray = arrayConfig("Size",[4 1],"ElementSpacing",2*lambda);
rxArray = arrayConfig("Size",[4 4],"ElementSpacing",lambda);

tx = txsite("cartesian", ...
    "Antenna",txArray, ...
    "AntennaPosition",[-44.799; -9.699; 1.245], ...
    'TransmitterFrequency',5.8e9);

rx = rxsite("cartesian", ...
    "Antenna",rxArray, ...
    "AntennaPosition",[8.757;0.710;1.245], ...
    "AntennaAngle",[0;90]);

siteviewer("SceneModel",mapFileName);
show(tx,"ShowAntennaHeight",false)
show(rx,"ShowAntennaHeight",false)

pm = propagationModel("raytracing", ...
    "CoordinateSystem","cartesian", ...
    "Method","sbr", ...
    "AngularSeparation","low", ...
    "MaxNumReflections",5);

rays = raytrace(tx,rx,pm);
plot(rays,"Colormap",jet,"ColorLimits",[50, 95])