%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%     ECUACIONES LINEALES PENDULO INVERTIDO SIMPLE EN ESPACIO DE ESTADOS    %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
pkg load control

g = 9.81; % m/s2 aceleracion de la gravedad
Lb = 270e-3; % Longitud de la barra en metros
da = 275.5e-3
mb = 35e-3; % Masa de la barra en Kg
ma = 10e-3; % Masa del extremo en Kg
m = mb + ma; % Masa total del conjunto
l = l = (mb*Lb/2 + ma*da) / m; % Longitud del centro de masas
J = (1/3)*mb*Lb^2 + ma*da^2; % Inercia total del sistema


% Matriz A
A = [0 1 0 0; m*g*l/J 0 0 0; 0 0 0 1; 0 0 0 0];
% Matriz B
B = [0; m*l/J; 0 ; 1];
% Matriz C
C = [1 0 0 0; 0 0 1 0];
% Matriz D
D = 0
% Sample Time 10 ms
Ts = 10e-3;
% Parametros máximos
theta_max = 0.1745; % 10 deg = 0.1745 radianes
theta_spd_max = 2; % 2 rad/s velocidad angulo
xmax = 0.2; % +/- 0.2 metros de carril
vmax = 0.5; % 0.5 m/s de carro
amax = 5; % 5 m/s² de carro

% Check Controllability and Observability
Co = ctrb(A, B);
Mo = obsv(A, C);
if rank(Co) < size(A,1), error('System not controllable'); end
if rank(Mo) < size(A,1), error('System not observable'); end

pendulum_ss=ss(A,B,C,D)
pendulum_ss_d=c2d(pendulum_ss,Ts)

Ad = pendulum_ss_d.A;
Bd = pendulum_ss_d.B;
Cd = pendulum_ss_d.C;
Dd = pendulum_ss_d.D;


% Matriz ponderacion de estados
Q = [1/theta_max^2, 0, 0, 0;
     0, 1/theta_spd_max^2, 0, 0;
     0, 0, 1/xmax^2, 0;
     0, 0, 0, 1/vmax^2];
R = 1/amax^2;

K = lqr(A,B,Q,R)
Kd = dlqr(Ad,Bd,Q,R)
lqr_poles = eig(Ad - Bd*Kd);
obs_poles = lqr_poles.^(4);

Lobs = place(Ad', Cd', obs_poles)';

x0 = [2*pi/180; 0; 0; 0];
pendulum_ss_d_cl = ss(Ad-Bd*Kd,Bd,Cd,Dd,Ts)
pendulum_ss_cl = ss(A-B*K,B,C,D)
figure()
initial(pendulum_ss_d_cl,x0)
figure()
pzmap(pendulum_ss_d_cl)
figure()
pzmap(pendulum_ss_cl)

A_aug = [Ad-Bd*Kd,      Bd*Kd;
         zeros(size(Ad)), Ad-Lobs*Cd];
B_aug = [Bd; zeros(size(Bd))];
C_aug = [Cd zeros(size(Cd))];
D_aug = Dd;
x0_aug = [x0; x0];

pendulum_ss_d_cl_oe = ss(A_aug,B_aug,C_aug,D_aug,Ts)
figure()
initial(pendulum_ss_d_cl_oe,x0_aug)


%% ========================================================================
%  EXPORTAR MATRICES A C++ PARA ESP32
%  ========================================================================

fprintf('\n\n');
fprintf('const float Ad[4][4] = {\n');
for i = 1:4
    fprintf('    {');
    for j = 1:4
        if j < 4
            fprintf('%.16gf, ', Ad(i,j));
        else
            fprintf('%.16gf', Ad(i,j));
        end
    end
    if i < 4
        fprintf('},\n');
    else
        fprintf('}};\n\n');
    end
end

fprintf('const float Bd[4] = {');
for i = 1:4
    if i < 4
        fprintf('%.16gf, ', Bd(i));
    else
        fprintf('%.16gf};\n\n', Bd(i));
    end
end

fprintf('const float K[4] = {');
for i = 1:4
    if i < 4
        fprintf('%.16gf, ', Kd(i));
    else
        fprintf('%.16gf};\n\n', Kd(i));
    end
end

fprintf('const float Lobs[4][2] = {\n');
for i = 1:4
    fprintf('    {');
    for j = 1:2
        if j < 2
            fprintf('%.16gf, ', Lobs(i,j));
        else
            fprintf('%.16gf', Lobs(i,j));
        end
    end
    if i < 4
        fprintf('},\n');
    else
        fprintf('}};\n');
    end
end
