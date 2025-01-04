function [ss] = close_in(filename, antPosSTA, antposition)
    % antPosSTA, antposition
    clc; close all;
    
    fc = 5.8e9;
    lambda = physconst("lightspeed") / fc;
    txArray = arrayConfig("Size", [4 1], "ElementSpacing", 2 * lambda);
    tx = txsite("cartesian", ...  %发射机
        "Antenna", txArray, ...
        "AntennaPosition", antposition, ...
        'TransmitterFrequency', 5.8e9);
    
    %接收机
    S = RandStream("mt19937ar", "Seed", 5489); % 创建一个随机数生成器对象，指定了种子为5489，以便重现结果。
    RandStream.setGlobalStream(S); %将全局随机数生成器设置为S，这样所有的随机函数都会使用S的设置。
    rxArraySize = [4 1];  % 定义一个接收天线阵列的大小，表示有4个天线元素排成一行。
    
    [RXs] = dlPositioningCreateEnvironment(rxArraySize, antPosSTA); %在分布方式为随机时，创建一个包含APs和STAs的环境模型，输入参数为天线阵列的大小和STAs的数量，输出参数为APs和STAs的位置和方向信息。
    
    distance = norm(antposition - antPosSTA);
    if distance < 0.0001
        % 使用射线追踪模型
        pm = propagationModel("raytracing", ...
            "CoordinateSystem","cartesian", ...
            "Method","sbr", ...
            "AngularSeparation","low", ...
            "MaxNumReflections",5);

        % 计算信号强度
        ss = sigstrength(RXs, tx, pm, "map", filename);
        
        % 如果射线追踪返回负无穷，使用 close-in 模型
        if isinf(ss) && ss < 0
            ss = sigstrength(RXs, tx, "close-in");
        end
    else
        % 使用 close-in 模型
        ss = sigstrength(RXs, tx, "close-in");
    end

    if isinf(ss) && ss < 0
        ss = -100;
    end

end

function [STAs] = dlPositioningCreateEnvironment(rxArraySize, antPosSTA)
    fc = 5.8e9; 
    lambda = physconst("lightspeed") / fc;
    rxArray = arrayConfig("Size", rxArraySize, "ElementSpacing", lambda);
    
    STAs = rxsite("cartesian", ...
        "Antenna", rxArray, ...
        "AntennaPosition", antPosSTA, ...
        "AntennaAngle", [0; 90]);
end
