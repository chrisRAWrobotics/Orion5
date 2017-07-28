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
    
    properties 
        % angles
        DEG = 0;
        RAD = 1;
        OFF = 56;
        
        % speed
        STANDARD = 0;
        RPM = 1;
        DEG_PER_SEC = 2;
        RAD_PER_SEC = 3;
        RPM_TO_DPS_RATIO = 6;
        RPM_TO_RPS_RATIO = 0.104719755;
        SET = 0;
        GET = 1;
        RPM_CONSTANT = 1023/112.83;
        
        % default settings
        defaultSpeedTypeSet = false;
        defaultSpeedType = 0;
       	defaultAngleSet = false;
        defaultAngle = 0;
        
        % string comparitives 
        RPM_POTENTIALS = {'rpm', 'revs per min', 'revolutionspermin', 'revolutions per min' 'revolutions_per_min', 'revolutionsperminute', 'revolutions per minute' 'revolutions_per_minute', 'r/m', 'revs/min', 'revolutions/minute'};
        DPS_POTENTIALS = {'dps','d_p_s', 'd/s', 'degrees per second', 'degrees/second', 'degreespersecond', 'degrees_per_second','degrees', 'deg_per_sec', 'deg/sec', 'degs/sec', 'deg/second', 'degs/second'};
        RPS_POTENTIALS = {'rps','r_p_s', 'r/s', 'radians per second', 'radians/second', 'radianspersecond', 'radians_per_second','radians', 'rad_per_sec', 'rad/sec', 'rads/sec', 'radss/second', 'rads/seconds'};
        OFF_POTENTIALS = {'off', 'turn off', 'none', 'no', 'of'};
        STANDARD_POTENTIALS = {'standard', 'normal'};
        DEG_POTENTIALS = {'deg','degs','d','degrees','degree'};
        RAD_POTENTIALS = {'rad','rads','r','radians','radian'};
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
                disp(strcat('Orion5: Unable to open socket: ', e));
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
        
        function setDefaultAngle(obj, degOrRad)
            try
                degOrRad = obj.checkAngleType(degOrRad);
                if degOrRad == obj.DEG
                    obj.defaultAngleSet = true;
                    obj.defaultAngle = obj.DEG;
                elseif degOrRad == obj.RAD
                    obj.defaultAngleSet = true;
                    obj.defaultAngle = obj.RAD;
                elseif degOrRad == obj.OFF
                    obj.defaultAngleSet = false;
                    obj.defaultAngle = obj.DEG;
                end
            catch errorMessage
                obj.stop()
                rethrow(errorMessage)
            end
        end
        
        function setDefaultSpeedType(obj, speedType)
            try
                if ischar(speedType)
                    speedType = obj.checkSpeedType(speedType);
                    if speedType == obj.STANDARD
                        obj.defaultSpeedType = obj.STANDARD;
                        obj.defaultSpeedTypeSet = true;
                    elseif speedType == obj.RPM
                        obj.defaultSpeedType = obj.RPM;
                        obj.defaultSpeedTypeSet = true;
                    elseif speedType == obj.RAD_PER_SEC
                        obj.defaultSpeedType = obj.RAD_PER_SEC;
                        obj.defaultSpeedTypeSet = true;
                    elseif speedType == obj.DEG_PER_SEC
                        obj.defaultSpeedType = obj.DEG_PER_SEC;
                        obj.defaultSpeedTypeSet = true;
                    elseif speedType == obj.OFF
                        obj.defaultSpeedType = obj.STANDARD;
                        obj.defaultSpeedTypeSet = false;
                    else 
                        error('Orion5: Default speed type not set, did not understand speed type. Please use standard, rpm, degs/sec or rads/sec');
                    end
                end
            catch errorMessage
                obj.stop()
                rethrow(errorMessage)
            end
        end
            
        function setAllJointsPosition(obj, positions, varargin)
            try
                invars = varargin;
                positions = obj.angleConversion(positions, invars);

                if ~all(size(positions) == [1 5])
                    error('Orion5: setAllJointsPosition requires an array of length 5');
                end
                positions = wrapTo360(positions);
                obj.setVar(0, 'posControl', '', positions);
            catch errorMessage
                obj.stop()
                rethrow(errorMessage)
            end
        end
        
        function setAllJointsSpeed(obj, speeds,varargin)
            try
                invars = varargin;
                speeds = obj.velocityConversions(speeds, obj.SET, invars);
                if ~all(size(speeds) == [1 5])
                    error('Orion5: setAllJointsSpeed requires an array of length 5');
                end
                obj.setVar(0, 'velControl', '', int32(speeds));
            catch errorMessage
                obj.stop()
                rethrow(errorMessage)
            end
        end
        
        function setAllJointsTorqueEnable(obj, enables)
            try
                if ~all(size(enables) == [1 5])
                    error('Orion5: setAllJointsTorqueEnable requires an array of length 5');
                end
                enables = ~~enables;
                obj.setVar(0, 'enControl', '', enables);
            catch errorMessage
                obj.stop
                rethrow(errorMessage)
            end
        end
        
        function setJointPosition(obj, jointID, pos, varargin)
            try
                invars = varargin;
                pos = obj.angleConversion(pos, invars);      
                pos = wrapTo360(pos);
                obj.setVar(jointID, 'control variables', 'goalPosition', pos);
            catch errorMessage
                obj.stop()
                rethrow(errorMessage)
            end
        end

        function setJointSpeed(obj, jointID, speed, varargin)
            try
                if ~any(obj.controlModes(jointID+1) == [obj.POS_SPEED, obj.VELOCITY])
                    error('Orion5: Control must be set to POS_SPEED or VELOCITY to use setJointSpeed');
                end
                invars = varargin;
                speed = obj.velocityConversion(speed, obj.SET, invars);
                obj.setVar(jointID, 'control variables', 'desiredSpeed', int32(speed));
            catch errorMessage
                obj.stop()
                rethrow(errorMessage)
            end
        end
        
        function setJointTimeToPosition(obj, jointID, seconds)
            try
                if ~(obj.controlModes(jointID+1) == obj.POS_TIME)
                    error('Orion5: Control mode must be set to POS_TIME to use setJointTimeToPosiion');
                end
                obj.setVar(jointID, 'control variables', 'desiredSpeed', int32(seconds * 10));
            catch errorMessage
                obj.stop()
                rethrow(errorMessage)
            end
        end
        
        function setJointControlMode(obj, jointID, controlMode)
            try
                if ~any(controlMode == [obj.POS_SPEED, obj.POS_TIME, obj.VELOCITY])
                    error('Orion5: controlMode not valid');
                end
                controlMode = int32(controlMode);
                obj.setVar(jointID, 'control variables', 'controlMode', controlMode);
                pause(1);
                obj.controlModes(jointID+1) = controlMode;
            catch errorMessage
                obj.stop()
                rethrow(errorMessage)
            end
        end
        
        function setJointTorqueEnable(obj, jointID, enable)
            try
                enable = ~~enable;
                obj.setVar(jointID, 'control variables', 'enable', enable);
            catch errorMessage
                obj.stop()
                rethrow(errorMessage)
            end
        end
        
        %% Getters
        function posArray = getAllJointsPosition(obj, varargin)
            try
                posArray = obj.getVar(0, 'posFeedback', '');
                invars = varargin;
                posArray = obj.angleConversion(posArray, invars);
            catch errorMessage
                obj.stop()
                rethrow(errorMessage)
            end
        end
        
        function speedArray = getAllJointsSpeed(obj, varargin)
            try
                invars = varargin;
                speedArray = obj.getVar(0, 'velFeedback', '');
                speedArray = obj.velocityConversion(speedArray, obj.GET, invars);
            catch errorMessage
                obj.stop()
                rethrow(errorMessage)
            end
        end
        
        function loadArray = getAllJointsLoad(obj)
            try
                loadArray = obj.getVar(0, 'torFeedback', '');
            catch errorMessage
                obj.stop()
                rethrow(errorMessage)
            end
        end
        
        function pos = getJointPosition(obj, jointID, varargin)
            try
                pos = obj.getVar(jointID, 'feedback variables', 'currentPosition');
                invars = varargin;
                pos = obj.angleConversion(pos, invars);
            catch errorMessage
                obj.stop()
                rethrow(errorMessage)
            end
        end
        
        function pos = getJointSpeed(obj, jointID, varargin)
            try
                invars = varargin;
                pos = obj.getVar(jointID, 'feedback variables', 'currentVelocity');
                pos = obj.velocityConversion(pos, obj.SET, invars);
            catch errorMessage
                obj.stop()
                rethrow(errorMessage)
            end
        end
        
        function pos = getJointLoad(obj, jointID)
            try
                pos = obj.getVar(jointID, 'feedback variables', 'currentLoad');
            catch errorMessage
                obj.stop()
                rethrow(errorMessage)
            end
        end
        
        %% Utility
        function vel = CWVelocity(~, vel)
            try
                vel = bitor(int32(vel), 1024);
            catch errorMessage
                obj.stop()
                rethrow(errorMessage)
            end
        end

        function vel = CCWVelocity(~, vel)
            try
                vel = int32(vel);
            catch errorMessage
                obj.stop()
                rethrow(errorMessage)
            end
        end
    end
   
    
    %% Private Methods
    methods (Access = 'private')
        function setVar(obj, jointID, id1, id2, value)
            if ~isa(obj.socket, 'tcpip')
                error('Orion5: Socket not opened yet');
            end
            
            if strcmp(id1, 'posControl')
                value = obj.vec2str(value, '%.2f,');
            elseif strcmp(id1, 'velControl')
                value = obj.vec2str(value, '%d,');
            elseif strcmp(id1, 'enControl')
                value = obj.vec2str(value, '%d,');
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
                if strcmp(id1, 'posFeedback') || strcmp(id1, 'velFeedback') || strcmp(id1, 'torFeedback')
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
        
         function pos = angleConversion(obj, pos, invars)
            if obj.defaultAngleSet == false
                if isempty(invars) == 1
                    degOrRad = obj.DEG;
                else
                    degOrRad = invars{1};
                    degOrRad = obj.checkAngleType(degOrRad);
                end
            else
                degOrRad = obj.defaultAngle;
            end
            if degOrRad == obj.RAD
                pos = deg2rad(pos);
            end
         end
          
         function velocity = velocityConversion(obj, velocity, direction, invars)
             if obj.defaultSpeedTypeSet == false
                if isempty(invars) == 1
                    speedType = obj.STANDARD;
                else
                    speedType = invars{1};
                    if ischar(speedType)
                        speedType = obj.checkSpeedType(speedType);
                    end
                end
             else
                 speedType = obj.defaultSpeedType;
             end
             if direction == 0
                 if speedType == obj.RPM
                     velocity = obj.rpm2standard(velocity);
                 elseif speedType == obj.DEG_PER_SEC
                     velocity = obj.dps2standard(velocity);
                 elseif speedType == obj.RAD_PER_SEC
                     velocity = obj.rps2standard(velocity);
                 end
                 if velocity > 1023
                     error('Orion5: velocity specified is greater than max speed');
                 end
            elseif direction == 1
                if speedType == obj.RPM
                     velocity = obj.standard2rpm(velocity);
                 elseif speedType == obj.DEG_PER_SEC
                     velocity = obj.standard2dps(velocity);
                 elseif speedType == obj.RAD_PER_SEC
                     velocity = obj.standard2rps(velocity);
                end
             end     
        end
         
          function degOrRad = checkAngleType(obj, degOrRad)
             if ischar(degOrRad)
                obj.OFF_POTENTIALS = {'off', 'turn off', 'none', 'no', 'of'};
                degOrRad = lower(degOrRad);
                if any(strcmp(degOrRad, obj.DEG_POTENTIALS))
                    degOrRad = obj.DEG;
                elseif any(strcmp(degOrRad, obj.RAD_POTENTIALS))
                    degOrRad = obj.RAD;
                elseif any(strcmp(degOrRad, obj.OFF_POTENTIALS))
                    degOrRad = obj.OFF;
                else
                    error('Orion5: degrees or radians specified but not understood, please indicate 0 for degrees or 1 for radians');
                end
             end
         end
         
         function speedType = checkSpeedType(obj, speedType)
            speedType = lower(speedType);
            if any(strcmp(speedType, obj.RPM_POTENTIALS))
                speedType = obj.RPM;
            elseif any(strcmp(speedType, obj.DPS_POTENTIALS))
                speedType = obj.DEG_PER_SEC;
            elseif any(strcmp(speedType, obj.RPS_POTENTIALS))
                speedType = obj.RAD_PER_SEC;
            elseif any(strcmp(speedType, obj.STANDARD_POTENTIALS))
                speedType = obj.STANDARD;
            elseif any(strcmp(speedType, obj.OFF_POTENTIALS))
                speedType = obj.OFF;
            else
                error('Orion5: speed specified but not understood, please indicate "standard", "rpm", "rads/sec" or "rads/min"');
            end
         end
         
        function velocity = rpm2standard(obj, velocity)
            velocity = round(obj.RPM_CONSTANT * velocity);
        end

        function velocity = standard2rpm(obj, velocity)
            velocity = velocity/obj.RPM_CONSTANT;
        end

        function velocity = standard2dps(obj, velocity)
            velocity = obj.standard2rpm(velocity);
            velocity = velocity*obj.RPM_TO_DPS_RATIO;
        end

        function velocity = dps2standard(obj, velocity)
            velocity = velocity/obj.RPM_TO_DPS_RATIO;
            velocity = round(obj.rpm2standard(velocity));
        end

        function velocity = standard2rps(obj, velocity)
            velocity = obj.standard2rpm(velocity);
            velocity = velocity * obj.RPM_TO_RPS_RATIO;
        end

        function velocity = rps2standard(obj, velocity)
            velocity = velocity/obj.RPM_TO_RPS_RATIO;
            velocity = round(obj.rpm2standard(velocity));
        end       
    end
    end

