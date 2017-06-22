clear all; clc;

orion = Orion5();
joint_angles = zeros(1, 5);

tic;
while 1
    % run for 10 seconds reading joint angles
    if toc > 10
        break;
    end
    
    for i = Orion5.BASE:Orion5.CLAW
        joint_angles(i+1) = orion.getJointPosition(i);
    end
    
    disp(joint_angles);
end

orion.stop();