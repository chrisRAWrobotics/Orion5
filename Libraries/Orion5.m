classdef Orion5 < handle
    properties (Constant)
        BASE = 0;
        SHOULDER = 1;
        ELBOW = 2;
        WRIST = 3;
        CLAW = 4;
    end
    
    properties (Access = 'private')
        socket = 0;
        tmr = 0;
        locked = 0;
    end

    methods
        function obj = Orion5()
            old_timer = timerfind('Name', 'Orion5KeepAlive')
            if ~isempty(old_timer)
                stop(old_timer);
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
        end
        
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
        
        function setJointPosition(obj, joint_index, pos)
           obj.setVar(joint_index, 'control variables', 'goalPosition', pos);
        end
        
        function setJointTimeToPosition(obj, joint_index, time)
           obj.setVar(joint_index, 'control variables', 'desiredSpeed', time);
        end
        
        function setJointTorqueEnable(obj, joint_index, enable)
            enable = ~~enable;
            obj.setVar(joint_index, 'control variables', 'enable', enable);
        end
        
        function pos = getJointPosition(obj, joint_index)
            pos = obj.getVar(joint_index, 'feedback variables', 'currentPosition');
        end
    end
    
    methods (Access = 'private')
        function setVar(obj, joint_index, id1, id2, value)
            if ~isa(obj.socket, 'tcpip')
                error('Orion5: Socket not opened yet');
            end            
            
            value = num2str(value);
            joint_index = num2str(joint_index);
            to_send = cell2mat({joint_index, '+', id1, '+', id2, '+', value});
            
            try
                fwrite(obj.socket, to_send);
            catch
                error('Orion5: Socket error, exiting.');
            end
        end
        
        function var = getVar(obj, joint_index, id1, id2)
            if ~isa(obj.socket, 'tcpip')
                error('Orion5: Socket not opened yet');
            end
            
            joint_index = num2str(joint_index);
            to_send = cell2mat({joint_index, '+', id1, '+', id2});
            
            try
                while obj.locked
                    pause(0.1);
                end
                obj.locked = 1;
                fwrite(obj.socket, to_send);
                while obj.socket.BytesAvailable < 1
                    pause(0.1);
                end
                var = native2unicode(fread(obj.socket, obj.socket.BytesAvailable)');
                var = str2double(var);
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
                    [~, num_bytes] = fread(obj.socket, 1);
                    if num_bytes < 1
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
    end
end