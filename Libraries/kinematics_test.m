close all; clear all;

path = [100 100; -100 100; -100 -100; 100 -100; 100 100;];
path_index = 1;

point_interval = 20;
points = [];

for i = 1:size(path, 1) - 1
    points = [points; path(i, :)];
    goal = path(i+1, :);
    
    dist = sqrt((goal(1) - points(end, 1))^2 + (goal(2) - points(end, 2))^2);
    
    for ii = 1:int32(dist/point_interval)
        [x, y] = pol2cart(atan2(goal(2) - points(end, 2), goal(1) - points(end, 1)), point_interval);
        points = [points; points(end, :) + [x y];];
    end
end

figure(2);
plot(points(:, 1), points(:,2), 'bx'); hold on;
plot(path(:, 1), path(:,2), 'bx', 'LineWidth', 2, 'MarkerSize', 10);
xlim([-300 300]); ylim([-300 300]);
grid on; grid minor;

for i = 1:size(points, 1)
    [t, r] = cart2pol(points(i, 1), points(i, 2));
    [j, m] = ikinematics(r, rad2deg(t), 100, -90, 20);
    if ~strcmp(m, '')
        j
        m
    end
end
