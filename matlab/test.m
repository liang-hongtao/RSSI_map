% mapFileName = '../../unreal_envs/room0902/BIg_Company_v2.stl';
% mapFileName = '/unreal_envs/Blg_Company_v2.stl';
mapFileName = 'unreal_envs/room0902/BIg_Company_v2.stl';
fc = 5.8e9;
lambda = physconst("lightspeed")/fc;
txArray = arrayConfig("Size",[4 1],"ElementSpacing",2*lambda);
rxArray = arrayConfig("Size",[4 4],"ElementSpacing",lambda);

% antposition = [-44.799; -9.699; 1.245];
antposition = [8.757; -9; 1.245];
tx = txsite("cartesian", ...
    "Antenna",txArray, ...
    "AntennaPosition", antposition, ...
    'TransmitterFrequency',5.8e9);

antPosSTA = [8.757;10;1.245];
rx = rxsite("cartesian", ...
    "Antenna",rxArray, ...
    "AntennaPosition",antPosSTA, ...
    "AntennaAngle",[0;90]);

distance = norm(antposition - antPosSTA);
% 根据距离选择传播模型
if distance < 20
    % 使用射线追踪模型
    pm = propagationModel("raytracing", ...
        "CoordinateSystem","cartesian", ...
        "Method","sbr", ...
        "AngularSeparation","low", ...
        "MaxNumReflections",5);

    % 计算信号强度
    ss = sigstrength(rx, tx, pm, "map", mapFileName);

    % 如果射线追踪返回负无穷，使用 close-in 模型
    if isinf(ss) && ss < 0
        ss = sigstrength(rx, tx, "close-in");
    end
else
    % 使用 close-in 模型
    ss = sigstrength(rx, tx, "close-in");
end

if isinf(ss) && ss < 0
    ss = -100;
end
ss
% siteviewer("SceneModel",mapFileName);
% show(tx,"ShowAntennaHeight",false)
% show(rx,"ShowAntennaHeight",false)
% 
% pm = propagationModel("raytracing", ...
%     "CoordinateSystem","cartesian", ...
%     "Method","sbr", ...
%     "AngularSeparation","low", ...
%     "MaxNumReflections",5);
% pm = propagationModel("freespace");
% rays = raytrace(tx,rx,pm);
% plot(rays,"Colormap",jet,"ColorLimits",[50, 95])

% sigstrength(rx, tx,"freespace")
% sigstrength(rx, tx,"close-in")

% sigstrength(rx, tx, pm, "map", mapFileName) %接收机,发射机,传播模型,地图