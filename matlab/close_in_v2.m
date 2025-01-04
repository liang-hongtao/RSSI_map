function [ss] = close_in_v2(filename, antPosSTA, antposition)
    % antPosSTA, antposition
    clc; close all;
    
    % 固定的频率和波长
    fc = 5.8e9;
    lambda = physconst("lightspeed") / fc;
    
    % 发射机天线阵列配置
    txArray = arrayConfig("Size", [1 1], "ElementSpacing", 2 * lambda);  % 只使用一个天线
    tx = txsite("cartesian", ...
        "Antenna", txArray, ...
        "AntennaPosition", antposition, ...
        'TransmitterFrequency', fc, ...
        'TransmitterPower', 50);  % 设置发射功率为 50 W
    
    % 确保使用固定的接收机配置
    rxArraySize = [1 1];  % 接收天线阵列大小
    [RXs] = dlPositioningCreateEnvironment(rxArraySize, antPosSTA);  % 创建接收环境

    % 计算信号强度，使用确定性传播模型
    ss = sigstrength(RXs, tx, "close-in");  % 使用close-in模型计算信号强度
    
    % 异常处理
    if isinf(ss) && ss < 0
        ss = -100;  % 若信号强度无效，返回 -100 dB
    end
end

function [STAs] = dlPositioningCreateEnvironment(rxArraySize, antPosSTA)
    fc = 5.8e9; 
    lambda = physconst("lightspeed") / fc;  % 波长
    rxArray = arrayConfig("Size", rxArraySize, "ElementSpacing", lambda);  % 接收天线阵列
    
    % 创建接收机，确保没有随机性
    STAs = rxsite("cartesian", ...
        "Antenna", rxArray, ...
        "AntennaPosition", antPosSTA, ...
        "AntennaAngle", [0; 90]);
end
