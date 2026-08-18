%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%     ECUACIONES LINEALES PENDULO INVERTIDO SIMPLE EN ESPACIO DE ESTADOS    %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
pkg load control

variations = 0.8:0.05:1.2;
g = 9.81; % m/s2 aceleracion de la gravedad
L = 300e-3; % Longitud de la barra en metros
mb = 35e-3; % Masa de la barra en Kg
ma0 = 10e-3;
ma = ma0*variations; % Masa del extremo en Kg

for i=1:1:length(variations)

  m = mb + ma(i); % Masa total del conjunto
  l = (mb*L/2+ma(i)*L)/(m); % Longitud del centro de masas
  J = 1/3*mb*L^2+ma(i)*L^2; % Inercia total del sistema


  % Matriz A
  A = [0 1 0 0; m*g*l/J 0 0 0; 0 0 0 1; 0 0 0 0];
  % Matriz B
  B = [0; m*l/J; 0 ; 1];
  % Matriz C
  C = [1 0 0 0; 0 0 1 0];
  % Matriz D
  D = 0;
  % Sample Time 10 ms
  Ts = 10e-3;
  % Parametros máximos
  theta_max = 0.1745; % 10 deg = 0.1745 radianes
  theta_spd_max = 2; % 2 rad/s velocidad angulo
  xmax = 0.2; % +/- 0.2 metros de carril
  vmax = 0.5; % 0.5 m/s de carro
  amax = 5; % 5 m/s² de carro

  pendulum_ss_d=c2d(ss(A,B,C,D),Ts);

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

  K_i(i,:) = dlqr(Ad,Bd,Q,R);

  K_table(i,:) = [ma(i) K_i(i,:)];
end

disp("      ma          K1          K2          K3          K4")
disp(K_table)
figure()
subplot(4,1,1)
plot(ma,K_i(:,1),'DisplayName','K1')
grid on; grid minor; box on;
ylabel('K1 [-]')
subplot(4,1,2)
plot(ma,K_i(:,2),'DisplayName','K2')
grid on; grid minor; box on;
ylabel('K2 [-]')
subplot(4,1,3)
plot(ma,K_i(:,3),'DisplayName','K3')
grid on; grid minor; box on;
ylabel('K3 [-]')
subplot(4,1,4)
plot(ma,K_i(:,4),'DisplayName','K4')
grid on; grid minor; box on;
ylabel('K4 [-]')
xlabel('Masa del extremo del pendulo "ma" [Kg]')



