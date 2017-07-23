clear all; clc;

orion = Orion5();

for id = Orion5.BASE:Orion5.WRIST
    orion.setJointTorqueEnable(id, 1);
    orion.setJointControlMode(id, Orion5.POS_TIME);
    orion.setJointTimeToPosition(id, 2);
end

state = 0;
angles = [];

tic;
counts = 0;
time = 0;
times = [];
while 1
    disp(orion.getAllJointsPosition());
    
    if (toc - time) > 5
        time = toc;
        state = ~state;
        counts = counts + 1;
        if counts > 10
            break
        end
        
        if state
            angles = ikinematics(100, 180, 300, 0, 250);
        else
            angles = ikinematics(150, 180, 100, 0, 20);
        end
        
        orion.setAllJointsPosition(angles);
    end
    
    pause(0.1); % pause so figure can update
end

orion.stop();