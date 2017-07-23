%% Orion 5 - MATLAB Library

classdef Orion5 < handle
    properties (Constant)
        % Joint IDs
        BASE = 0;
        SHOULDER = 1;
        ELBOW = 2;
        WRIST = 3;
        CLAW = 4;
        
        % Control Modes
        POS_SPEED = 0;
        POS_TIME = 1;
        VELOCITY = 2;
    end
    
    properties (Access = 'private')
        socket = 0;
        tmr = 0;
        locked = 0;
        controlModes = zeros(1, 5);
    end
    
    %% Public Methods
    methods
        %% Constructor
        function obj = Orion5()
            oldTimer = timerfind('Name', 'Orion5KeepAlive');
            if ~isempty(oldTimer)
                stop(oldTimer);
            end
            
            try
                obj.socket = tcpip('127.0.0.1', 42000, 'NetworkRole', 'client', 'Timeout', 2.5);
                fopen(obj.socket);
            catch e
                obj.socket = 0;
                error(strcat('Orion5: Unable to open socket: '), e);
            end
            
            obj.tmr = timer('Period', 1, 'Name', 'Orion5KeepAlive', 'ExecutionMode', 'fixedSpacing', 'TimerFcn', @obj.keepAliveFcn);
            start(obj.tmr);
            
            pause(3);
        end
        
        %% Cleanup Functions
        function stop(obj)
            obj.delete()
        end
        
        function delete(obj)
            disp('Orion5: Cleaning up.');
            if isa(obj.tmr, 'timer')
                stop(obj.tmr);
                delete(obj.tmr);
            end
            if isa(obj.socket, 'tcpip')
                fwrite(obj.socket, 'q');
                fclose(obj.socket);
            end
        end
        
        %% Setters
        function setAllJointsPosition(obj, positions)
            if ~all(size(positions) == [1 5])
                error('Orion5: setAllJointsPosition requires an array of length 5');
            end
            positions = wrapTo360(positions);
            obj.setVar(0, 'posControl', '', positions);
        end
        
        function setAllJointsSpeed(obj, speeds)
            if ~all(size(speeds) == [1 5])
                error('Orion5: setAllJointsSpeed requires an array of length 5');
            end
            obj.setVar(0, 'velControl', '', int32(speeds));
        end
        
        function setAllJointsTorqueEnable(obj, enables)
            if ~all(size(enables) == [1 5])
                error('Orion5: setAllJointsTorqueEnable requires an array of length 5');
            end
            enables = ~~enables;
            obj.setVar(0, 'enControl', '', enables);
        end
        
        function setJointPosition(obj, jointID, pos)
            pos = wrapTo360(pos);
        	obj.setVar(jointID, 'control variables', 'goalPosition', pos);
        end

        function setJointSpeed(obj, jointID, speed)
            if ~any(obj.controlModes(jointID+1) == [obj.POS_SPEED, obj.VELOCITY])
                error('Orion5: Control must be set to POS_SPEED or VELOCITY to use setJointSpeed');
            end
        	obj.setVar(jointID, 'control variables', 'desiredSpeed', int32(speed));
        end
        
        function setJointTimeToPosition(obj, jointID, seconds)
            if ~(obj.controlModes(jointID+1) == obj.POS_TIME)
                error('Orion5: Control mode must be set to POS_TIME to use setJointTimeToPosiion');
            end
        	obj.setVar(jointID, 'control variables', 'desiredSpeed', int32(seconds * 10));
        end
        
        function setJointControlMode(obj, jointID, controlMode)
            if ~any(controlMode == [obj.POS_SPEED, obj.POS_TIME, obj.VELOCITY])
                error('Orion5: controlMode not valid');
            end
            controlMode = int32(controlMode);
            obj.setVar(jointID, 'control variables', 'controlMode', controlMode);
            pause(1);
            obj.controlModes(jointID+1) = controlMode;
        end
        
        function setJointTorqueEnable(obj, jointID, enable)
            enable = ~~enable;
            obj.setVar(jointID, 'control variables', 'enable', enable);
        end
        
        %% Getters
        function posArray = getAllJointsPosition(obj)
            posArray = obj.getVar(0, 'posFeedback', '');
        end
        
        function speedArray = getAllJointsSpeed(obj)
            speedArray = obj.getVar(0, 'velFeedback', '');
        end
        
        function loadArray = getAllJointsLoad(obj)
            loadArray = obj.getVar(0, 'torFeedback', '');
        end
        
        function pos = getJointPosition(obj, jointID)
            pos = obj.getVar(jointID, 'feedback variables', 'currentPosition');
        end
        
        function pos = getJointSpeed(obj, jointID)
            pos = obj.getVar(jointID, 'feedback variables', 'currentVelocity');
        end
        
        function pos = getJointLoad(obj, jointID)
            pos = obj.getVar(jointID, 'feedback variables', 'currentLoad');
        end
        
        %% Utility
        function vel = CWVelocity(~, vel)
            vel = bitor(int32(vel), 1024);
        end

        function vel = CCWVelocity(~, vel)
            vel = int32(vel);
        end
    end
    
    %% Private Methods
    methods (Access = 'private')
        function setVar(obj, jointID, id1, id2, value)
            if ~isa(obj.socket, 'tcpip')
                error('Orion5: Socket not opened yet');
            end
            
            if strcmp(id1, 'posControl')
                value = vec2str(value, '%.2f,');
            elseif strcmp(id1, 'velControl')
                value = vec2str(value, '%d,');
            elseif strcmp(id1, 'enControl')
                value = vec2str(value, '%d,');
            else
                value = num2str(value);
            end
            jointID = num2str(jointID);
            to_send = cell2mat({jointID, '+', id1, '+', id2, '+', value});
            
            try
                fwrite(obj.socket, to_send);
            catch
                error('Orion5: Socket error, exiting.');
            end
        end
        
        function var = getVar(obj, jointID, id1, id2)
            if ~isa(obj.socket, 'tcpip')
                error('Orion5: Socket not opened yet');
            end
            
            jointID = num2str(jointID);
            to_send = cell2mat({jointID, '+', id1, '+', id2});
            
            try
                while obj.locked
                    pause(0.01);
                end
                obj.locked = 1;
                fwrite(obj.socket, to_send);
                while obj.socket.BytesAvailable < 1
                    
                end
                var = native2unicode(fread(obj.socket, obj.socket.BytesAvailable)');
                if strcmp(id1, 'posFeedback')
                    var = eval(var);
                else
                    var = str2double(var);
                end
            catch
                var = 0;
                error('Orion5: Socket error, exiting.');
            end
            obj.locked = 0;
        end
        
        function keepAliveFcn(obj, ~, ~)
            if ~obj.locked
                try
                    obj.locked = 1;
                    fwrite(obj.socket, 'p');
                    [~, numBytes] = fread(obj.socket, 1);
                    if numBytes < 1
                        warning('Orion5: No response from server, exiting.');
                        obj.delete();
                    end
                catch
                    warning('Orion5: Socket error, exiting.');
                    obj.delete();
                end
                obj.locked = 0;
            end
        end

        function str = vec2str(~, vec, format)
            str = sprintf(format, vec);
            str(end) = ']';
            str = strcat('[', str);
        end
    end
end
