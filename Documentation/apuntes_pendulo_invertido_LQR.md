
# Péndulo invertido y control LQR — Apuntes completos

> [!INFO]
> Estos apuntes reorganizan y limpian los apuntes manuscritos, manteniendo el desarrollo matemático paso a paso.
> Se han corregido algunas erratas de signo, traspuestas y notación. Al final hay una sección específica con las correcciones más importantes.

---

# 1. Modelo mecánico mediante Lagrange

## 1.1. Coordenadas y geometría

Consideramos un péndulo invertido montado sobre un carro que se desplaza horizontalmente.

Tomamos como coordenadas generalizadas:

$$
q=
\begin{bmatrix}
x\\
\theta
\end{bmatrix}
$$

donde:

- $x(t)$: posición horizontal del carro.
- $\theta(t)$: ángulo del péndulo medido respecto a la vertical superior.
- $L$: distancia desde el punto de giro hasta la masa puntual del péndulo.
- $m$: masa del péndulo.
- $g$: aceleración de la gravedad.

Con la convención geométrica empleada en los apuntes:

$$
x_p = x - L\sin\theta
$$

$$
y_p = L\cos\theta
$$

donde $(x_p,y_p)$ es la posición de la masa del péndulo.

---

## 1.2. Velocidad de la masa del péndulo

Derivamos respecto al tiempo.

Para $x_p$:

$$
x_p=x-L\sin\theta
$$

$$
\dot x_p
=
\dot x
-
L\cos\theta\,\dot\theta
$$

porque:

$$
\frac{d}{dt}\sin\theta(t)
=
\cos\theta\,\dot\theta
$$

Para $y_p$:

$$
y_p=L\cos\theta
$$

$$
\dot y_p
=
-L\sin\theta\,\dot\theta
$$

El módulo de la velocidad al cuadrado es:

$$
v_p^2
=
\dot x_p^2+\dot y_p^2
$$

Sustituyendo:

$$
v_p^2
=
\left(
\dot x-L\dot\theta\cos\theta
\right)^2
+
\left(
-L\dot\theta\sin\theta
\right)^2
$$

Desarrollando:

$$
v_p^2
=
\dot x^2
-2\dot xL\dot\theta\cos\theta
+
L^2\dot\theta^2\cos^2\theta
+
L^2\dot\theta^2\sin^2\theta
$$

Usando:

$$
\sin^2\theta+\cos^2\theta=1
$$

queda:

$$
\boxed{
v_p^2
=
\dot x^2
-2\dot xL\dot\theta\cos\theta
+
L^2\dot\theta^2
}
$$

---

# 2. Energía cinética y potencial

## 2.1. Energía cinética

Para una masa puntual:

$$
T=\frac12mv_p^2
$$

Por tanto:

$$
\boxed{
T
=
\frac12m
\left(
\dot x^2
-2\dot xL\dot\theta\cos\theta
+
L^2\dot\theta^2
\right)
}
$$

> [!NOTE]
> Este modelo supone una masa puntual situada a distancia $L$ del eje.
> Si se modelara una barra rígida con momento de inercia propio, habría que añadir el término rotacional correspondiente.

---

## 2.2. Energía potencial

La energía potencial gravitatoria es:

$$
V=mgy
$$

y como:

$$
y_p=L\cos\theta
$$

tenemos:

$$
\boxed{
V=mgL\cos\theta
}
$$

---

# 3. Lagrangiano

El Lagrangiano se define como:

$$
\boxed{
\mathcal L=T-V
}
$$

Por tanto:

$$
\mathcal L
=
\frac12m\dot x^2
-
m\dot xL\dot\theta\cos\theta
+
\frac12mL^2\dot\theta^2
-
mgL\cos\theta
$$

---

# 4. De la acción a Euler-Lagrange

La acción es:

$$
\boxed{
S[q]=\int_{t_1}^{t_2}
\mathcal L(q,\dot q,t)\,dt
}
$$

El principio variacional impone:

$$
\delta S=0
$$

para una trayectoria física sin fuerzas generalizadas externas.

La variación de $\mathcal L$ es:

$$
\delta\mathcal L
=
\frac{\partial\mathcal L}{\partial q}\delta q
+
\frac{\partial\mathcal L}{\partial\dot q}\delta\dot q
$$

y:

$$
\delta\dot q
=
\frac{d}{dt}(\delta q)
$$

Entonces:

$$
\delta S
=
\int_{t_1}^{t_2}
\left[
\frac{\partial\mathcal L}{\partial q}\delta q
+
\frac{\partial\mathcal L}{\partial\dot q}
\frac{d}{dt}(\delta q)
\right]dt
$$

Integramos por partes el segundo término:

$$
\int
\frac{\partial\mathcal L}{\partial\dot q}
\frac{d}{dt}(\delta q)\,dt
=
\left[
\frac{\partial\mathcal L}{\partial\dot q}\delta q
\right]_{t_1}^{t_2}
-
\int
\frac{d}{dt}
\left(
\frac{\partial\mathcal L}{\partial\dot q}
\right)
\delta q\,dt
$$

Como los extremos están fijados:

$$
\delta q(t_1)=\delta q(t_2)=0
$$

el término de contorno desaparece.

Queda:

$$
\delta S
=
\int_{t_1}^{t_2}
\left[
\frac{\partial\mathcal L}{\partial q}
-
\frac{d}{dt}
\left(
\frac{\partial\mathcal L}{\partial\dot q}
\right)
\right]
\delta q\,dt
$$

Como $\delta q$ es arbitrario:

$$
\boxed{
\frac{d}{dt}
\left(
\frac{\partial\mathcal L}{\partial\dot q}
\right)
-
\frac{\partial\mathcal L}{\partial q}
=0
}
$$

---

# 5. Fuerzas generalizadas externas

Si existe una fuerza generalizada externa $Q$, el principio variacional se expresa como:

$$
\delta S+\delta W=0
$$

con:

$$
\delta W
=
\int Q\,\delta q\,dt
$$

Entonces:

$$
\boxed{
\frac{d}{dt}
\left(
\frac{\partial\mathcal L}{\partial\dot q}
\right)
-
\frac{\partial\mathcal L}{\partial q}
=
Q
}
$$

Para el sistema carro-péndulo:

$$
q=
\begin{bmatrix}
x\\
\theta
\end{bmatrix}
$$

La coordenada del carro está asociada a la fuerza externa aplicada por el actuador, mientras que para el ángulo del péndulo no se aplica directamente ningún par:

$$
Q_x\neq0,
\qquad
Q_\theta=0
$$

---

# 6. Ecuación de Euler-Lagrange para $\theta$

Nos centramos en la ecuación angular:

$$
\frac{d}{dt}
\left(
\frac{\partial\mathcal L}{\partial\dot\theta}
\right)
-
\frac{\partial\mathcal L}{\partial\theta}
=0
$$

Partimos de:

$$
\mathcal L
=
\frac12m\dot x^2
-
m\dot xL\dot\theta\cos\theta
+
\frac12mL^2\dot\theta^2
-
mgL\cos\theta
$$

## 6.1. Derivada respecto a $\dot\theta$

$$
\frac{\partial\mathcal L}{\partial\dot\theta}
=
-m\dot xL\cos\theta
+
mL^2\dot\theta
$$

Derivamos respecto al tiempo:

$$
\frac{d}{dt}
\left(
\frac{\partial\mathcal L}{\partial\dot\theta}
\right)
=
-mL\ddot x\cos\theta
+
mL\dot x\dot\theta\sin\theta
+
mL^2\ddot\theta
$$

---

## 6.2. Derivada respecto a $\theta$

Los términos dependientes de $\theta$ son:

$$
-m\dot xL\dot\theta\cos\theta
-
mgL\cos\theta
$$

Por tanto:

$$
\frac{\partial\mathcal L}{\partial\theta}
=
m\dot xL\dot\theta\sin\theta
+
mgL\sin\theta
$$

---

## 6.3. Sustitución en Euler-Lagrange

$$
-mL\ddot x\cos\theta
+
mL\dot x\dot\theta\sin\theta
+
mL^2\ddot\theta
-
m\dot xL\dot\theta\sin\theta
-
mgL\sin\theta
=0
$$

Los términos cruzados se cancelan:

$$
mL\dot x\dot\theta\sin\theta
-
mL\dot x\dot\theta\sin\theta
=0
$$

y obtenemos:

$$
\boxed{
-mL\ddot x\cos\theta
+
mL^2\ddot\theta
-
mgL\sin\theta
=0
}
$$

Dividiendo por $mL$:

$$
\boxed{
-\ddot x\cos\theta
+
L\ddot\theta
-
g\sin\theta
=0
}
$$

o:

$$
\boxed{
\ddot\theta
=
\frac{\ddot x}{L}\cos\theta
+
\frac{g}{L}\sin\theta
}
$$

Esta es la dinámica angular no lineal del modelo usado aquí.

---

# 7. Aproximación de ángulo pequeño

Alrededor de la posición vertical:

$$
|\theta|\ll1
$$

con $\theta$ expresado en radianes.

Mediante Taylor:

$$
\sin\theta
=
\theta-\frac{\theta^3}{3!}+\frac{\theta^5}{5!}-\cdots
$$

y:

$$
\cos\theta
=
1-\frac{\theta^2}{2!}+\frac{\theta^4}{4!}-\cdots
$$

Para una linealización de primer orden:

$$
\boxed{
\sin\theta\approx\theta
}
$$

$$
\boxed{
\cos\theta\approx1
}
$$

Aplicando estas aproximaciones:

$$
-\ddot x
+
L\ddot\theta
-
g\theta
=
0
$$

por tanto:

$$
\boxed{
\ddot\theta
=
\frac{g}{L}\theta
+
\frac{1}{L}\ddot x
}
$$

---

# 8. Espacio de estados

Definimos:

$$
x_1=\theta
$$

$$
x_2=\dot\theta
$$

$$
x_3=x
$$

$$
x_4=\dot x
$$

y tomamos como entrada:

$$
\boxed{
u=\ddot x
}
$$

Entonces:

$$
\dot x_1=x_2
$$

$$
\dot x_2
=
\frac{g}{L}x_1
+
\frac{1}{L}u
$$

$$
\dot x_3=x_4
$$

$$
\dot x_4=u
$$

En forma matricial:

$$
\boxed{
\dot{\mathbf x}=A\mathbf x+B u
}
$$

con:

$$
A=
\begin{bmatrix}
0&1&0&0\\
\frac{g}{L}&0&0&0\\
0&0&0&1\\
0&0&0&0
\end{bmatrix}
$$

y:

$$
B=
\begin{bmatrix}
0\\
\frac{1}{L}\\
0\\
1
\end{bmatrix}
$$

> [!NOTE]
> Aquí se ha abstraído toda la dinámica del actuador.
> El controlador LQR calcula una aceleración deseada del carro:
>
> $$
> u=\ddot x
> $$
>
> y después la implementación real deberá convertir esa aceleración deseada en comandos al TMC/stepper.

---

# 9. Estimación de los estados del carro

Si no existe encoder en el carro, se puede estimar su posición suponiendo que no hay pérdida de pasos.

Si cada paso produce un desplazamiento lineal $\Delta x_{\text{step}}$:

$$
\boxed{
x
=
N_{\text{steps}}\Delta x_{\text{step}}
}
$$

respecto al origen de control elegido.

La velocidad puede obtenerse mediante la frecuencia de pasos o, aproximadamente:

$$
\boxed{
\dot x
\approx
\frac{x_k-x_{k-1}}{\Delta t}
}
$$

La hipótesis fundamental es:

$$
\boxed{
N_{\text{pasos comandados}}
=
N_{\text{pasos ejecutados}}
}
$$

Si el motor pierde pasos, la estimación de $x$ deja de coincidir con la posición física real.

---

# 10. Problema LQR

Queremos realimentar los estados:

$$
\boxed{
u=-Kx
}
$$

Para cuatro estados:

$$
K=
\begin{bmatrix}
k_1&k_2&k_3&k_4
\end{bmatrix}
$$

y:

$$
u
=
-k_1\theta
-k_2\dot\theta
-k_3x
-k_4\dot x
$$

La pregunta inicial es:

> ¿Qué condiciones debe cumplir $K$ para que el sistema sea estable?

Después aparecerá una segunda pregunta:

> Entre todos los $K$ estabilizantes, ¿cuál minimiza el coste que yo he definido?

---

# 11. LQR de horizonte finito

Para un sistema lineal:

$$
\dot x=Ax+Bu
$$

un coste cuadrático general de horizonte finito puede escribirse como:

$$
J=
x^T(t_f)F\,x(t_f)
+
\int_{t_0}^{t_f}
\left(
x^TQx
+
u^TRu
+
2x^TNu
\right)dt
$$

donde:

- $F$: matriz de coste terminal.
- $Q$: matriz de coste de estado.
- $R$: matriz de coste de control.
- $N$: matriz de coste cruzado estado-control.

La ley óptima tiene forma:

$$
u=-K(t)x
$$

con:

$$
K(t)
=
R^{-1}
\left(
B^TP(t)+N^T
\right)
$$

y $P(t)$ satisface la ecuación diferencial de Riccati:

$$
-\dot P
=
A^TP+PA
-
(PB+N)R^{-1}(B^TP+N^T)
+
Q
$$

con condición terminal:

$$
\boxed{
P(t_f)=F
}
$$

> [!IMPORTANT]
> En horizonte finito, $P$ depende del tiempo:
>
> $$
> P=P(t)
> $$
>
> y por tanto:
>
> $$
> K=K(t)
> $$
>
> Esto significa que la política óptima depende de cuánto tiempo queda hasta el final del horizonte.

---

# 12. Paso al horizonte infinito

En el LQR continuo de horizonte infinito se utiliza normalmente:

$$
\boxed{
J=
\int_0^\infty
\left(
x^TQx+u^TRu
\right)dt
}
$$

En esta formulación estándar:

- no hay término terminal finito,
- tomamos $N=0$,
- bajo las condiciones habituales de estabilizabilidad y detectabilidad, $P(t)$ converge a una matriz constante $P$.

En régimen estacionario:

$$
\dot P=0
$$

y la ecuación diferencial de Riccati se convierte en la ecuación algebraica de Riccati:

$$
\boxed{
A^TP+PA
-
PBR^{-1}B^TP
+
Q
=
0
}
$$

La ganancia queda:

$$
\boxed{
K=R^{-1}B^TP
}
$$

---

# 13. Selección de $Q$ y $R$

La función de coste es:

$$
J=
\int_0^\infty
\left(
x^TQx+u^TRu
\right)dt
$$

$Q$ determina cuánto penalizamos los errores de estado.

$R$ determina cuánto penalizamos el esfuerzo de control.

Para:

$$
x=
\begin{bmatrix}
\theta&
\dot\theta&
x&
\dot x
\end{bmatrix}^T
$$

una elección diagonal es:

$$
Q=
\begin{bmatrix}
q_\theta&0&0&0\\
0&q_{\dot\theta}&0&0\\
0&0&q_x&0\\
0&0&0&q_{\dot x}
\end{bmatrix}
$$

---

## 13.1. Regla de Bryson

Una regla de normalización útil es:

$$
\boxed{
Q_{ii}=\frac{1}{x_{i,\max}^2}
}
$$

y:

$$
\boxed{
R_{jj}=\frac{1}{u_{j,\max}^2}
}
$$

Para unos valores de diseño, por ejemplo:

$$
\theta_{\max}
=
10^\circ
=
0.1745\text{ rad}
$$

$$
\dot\theta_{\max}
=
2\text{ rad/s}
$$

$$
x_{\max}
=
0.20\text{ m}
$$

$$
\dot x_{\max}
=
0.5\text{ m/s}
$$

$$
u_{\max}
=
\ddot x_{\max}
=
5\text{ m/s}^2
$$

tendríamos:

$$
Q
=
\operatorname{diag}
\left(
\frac{1}{0.1745^2},
\frac{1}{2^2},
\frac{1}{0.2^2},
\frac{1}{0.5^2}
\right)
$$

y:

$$
R
=
\frac{1}{5^2}
$$

> [!NOTE]
> $x_{\max}$ no representa necesariamente un límite físico impuesto por el LQR.
> Es una escala de ponderación: expresa cuánto queremos penalizar el desplazamiento respecto al punto de referencia.

---

# 14. Primera pregunta: estabilidad mediante Lyapunov

Partimos de:

$$
\dot x=Ax+Bu
$$

y proponemos:

$$
\boxed{
u=-Kx
}
$$

Entonces:

$$
\dot x
=
Ax-BKx
$$

$$
\boxed{
\dot x
=
(A-BK)x
}
$$

Definimos:

$$
\boxed{
A_{cl}=A-BK
}
$$

de modo que:

$$
\dot x=A_{cl}x
$$

---

## 14.1. Función candidata de Lyapunov

Elegimos:

$$
\boxed{
V(x)=x^TPx
}
$$

con:

$$
P=P^T>0
$$

Para que $V$ pueda usarse como función de Lyapunov necesitamos:

$$
V(x)>0
\qquad
\forall x\neq0
$$

y:

$$
V(0)=0
$$

---

## 14.2. Derivada temporal de $V$

Como:

$$
V=x^TPx
$$

y $P$ es constante:

$$
\dot V
=
\dot x^TPx
+
x^TP\dot x
$$

Sustituimos:

$$
\dot x=A_{cl}x
$$

Entonces:

$$
\dot x^T
=
x^TA_{cl}^T
$$

y:

$$
\dot V
=
x^TA_{cl}^TPx
+
x^TPA_{cl}x
$$

Agrupando:

$$
\boxed{
\dot V
=
x^T
\left(
A_{cl}^TP+PA_{cl}
\right)x
}
$$

Para estabilidad asintótica queremos:

$$
\boxed{
A_{cl}^TP+PA_{cl}<0
}
$$

con:

$$
P>0
$$

Si existe una matriz $P=P^T>0$ que satisface esta desigualdad, entonces $A_{cl}$ es Hurwitz, es decir:

$$
\boxed{
\Re\{\lambda_i(A_{cl})\}<0
\qquad
\forall i
}
$$

> [!IMPORTANT]
> No es correcto decir que "$A_{cl}$ debe ser negativa".
>
> El criterio es que $A_{cl}$ sea **Hurwitz**, no que todos sus elementos sean negativos.

Hasta aquí Lyapunov responde:

> **¿Este $K$ estabiliza el sistema?**

Pero todavía no nos dice cuál de todos los $K$ estabilizantes es el mejor.

---

# 15. Segunda pregunta: ¿qué $K$ es óptimo?

Ahora queremos el $K$ que minimice:

$$
\boxed{
J=
\int_0^\infty
\left(
x^TQx+u^TRu
\right)dt
}
$$

Interpretación:

- $x^TQx$: coste debido al error de los estados.
- $u^TRu$: coste debido al esfuerzo de control.

---

# 16. Función de valor de Bellman

Definimos:

$$
\boxed{
V(x)
=
\min_{u(\cdot)}J
}
$$

$V(x)$ representa:

> el coste mínimo total que todavía tendremos que pagar desde el estado actual $x$ hasta el horizonte infinito.

Para LQR proponemos una función de valor cuadrática:

$$
\boxed{
V(x)=x^TPx
}
$$

donde $P$ es desconocida.

Esta hipótesis es coherente con la estructura del problema:

- dinámica lineal,
- coste cuadrático.

---

# 17. Principio de optimalidad de Bellman

Supongamos que estamos en el estado $x$.

Durante un intervalo infinitesimal $dt$ pagamos:

$$
\left(
x^TQx+u^TRu
\right)dt
$$

Después de ese intervalo el estado será:

$$
x+dx
$$

Por tanto:

$$
\boxed{
V(x)
=
\min_u
\left[
\left(
x^TQx+u^TRu
\right)dt
+
V(x+dx)
\right]
}
$$

La idea es:

$$
\boxed{
\text{coste óptimo actual}
=
\text{coste inmediato}
+
\text{coste óptimo futuro}
}
$$

No hemos eliminado la integral de manera arbitraria.

Simplemente hemos separado:

$$
\int_t^\infty
=
\int_t^{t+dt}
+
\int_{t+dt}^{\infty}
$$

y para el intervalo infinitesimal:

$$
\int_t^{t+dt}
\ell(x,u)\,d\tau
\approx
\ell(x,u)\,dt
$$

---

# 18. Expansión de Taylor de $V(x+dx)$

Para un $dx$ infinitesimal:

$$
V(x+dx)
\approx
V(x)
+
\frac{\partial V}{\partial x}dx
$$

Como:

$$
dx=\dot x\,dt
$$

y:

$$
\dot x=Ax+Bu
$$

tenemos:

$$
dx=(Ax+Bu)dt
$$

Por tanto:

$$
V(x+dx)
\approx
V(x)
+
\frac{\partial V}{\partial x}
(Ax+Bu)dt
$$

Sustituimos en Bellman:

$$
V(x)
=
\min_u
\left[
(x^TQx+u^TRu)dt
+
V(x)
+
\frac{\partial V}{\partial x}
(Ax+Bu)dt
\right]
$$

Restamos $V(x)$ en ambos lados:

$$
0
=
\min_u
\left[
(x^TQx+u^TRu)dt
+
\frac{\partial V}{\partial x}
(Ax+Bu)dt
\right]
$$

Dividimos por $dt$:

$$
\boxed{
0
=
\min_u
\left[
x^TQx
+
u^TRu
+
\frac{\partial V}{\partial x}
(Ax+Bu)
\right]
}
$$

Esta es la ecuación de Hamilton-Jacobi-Bellman estacionaria.

---

# 19. Derivada de $V=x^TPx$ respecto a $x$

Tenemos:

$$
V=x^TPx
$$

La diferencial es:

$$
dV
=
d(x^TPx)
$$

Como $P$ es constante:

$$
dV
=
(dx)^TPx
+
x^TP(dx)
$$

El primer término puede escribirse como:

$$
(dx)^TPx
=
x^TP^Tdx
$$

Entonces:

$$
dV
=
x^T(P^T+P)dx
$$

Como:

$$
P=P^T
$$

queda:

$$
dV
=
2x^TP\,dx
$$

Por definición:

$$
dV
=
\frac{\partial V}{\partial x}dx
$$

por tanto, usando la convención de gradiente fila:

$$
\boxed{
\frac{\partial V}{\partial x}
=
2x^TP
}
$$

Equivalentemente, si se usa gradiente columna:

$$
\boxed{
\nabla_xV
=
2Px
}
$$

---

# 20. HJB con la función de valor cuadrática

Sustituimos:

$$
\frac{\partial V}{\partial x}
=
2x^TP
$$

en HJB:

$$
0
=
\min_u
\left[
x^TQx
+
u^TRu
+
2x^TP(Ax+Bu)
\right]
$$

Desarrollando:

$$
\boxed{
0
=
\min_u
\left[
x^TQx
+
u^TRu
+
2x^TPAx
+
2x^TPBu
\right]
}
$$

---

# 21. Minimización respecto a $u$

Los términos dependientes de $u$ son:

$$
u^TRu
+
2x^TPBu
$$

Derivamos respecto a $u$.

Como $R=R^T$:

$$
\frac{\partial}{\partial u}
(u^TRu)
=
2Ru
$$

y:

$$
\frac{\partial}{\partial u}
(2x^TPBu)
=
2B^TPx
$$

La condición de mínimo es:

$$
2Ru+2B^TPx=0
$$

Dividiendo por 2:

$$
Ru+B^TPx=0
$$

por tanto:

$$
\boxed{
u^*
=
-R^{-1}B^TPx
}
$$

Queríamos una ley de la forma:

$$
u=-Kx
$$

Así que:

$$
\boxed{
K
=
R^{-1}B^TP
}
$$

> [!IMPORTANT]
> La ganancia $K$ **no lleva signo negativo**.
>
> El signo negativo ya está contenido en la ley:
>
> $$
> u=-Kx
> $$

Todavía no conocemos $P$.

---

# 22. Sustitución del control óptimo en HJB

Partimos de:

$$
0
=
x^TQx
+
u^TRu
+
2x^TPAx
+
2x^TPBu
$$

y sustituimos:

$$
u^*
=
-R^{-1}B^TPx
$$

---

## 22.1. Cálculo de $u^TRu$

Primero:

$$
u^T
=
-x^TP^TBR^{-T}
$$

Como:

$$
P=P^T
$$

y:

$$
R=R^T
$$

también:

$$
R^{-T}=R^{-1}
$$

entonces:

$$
u^T
=
-x^TPBR^{-1}
$$

Por tanto:

$$
u^TRu
=
x^TPBR^{-1}RR^{-1}B^TPx
$$

y:

$$
\boxed{
u^TRu
=
x^TPBR^{-1}B^TPx
}
$$

---

## 22.2. Cálculo de $2x^TPBu$

$$
2x^TPBu
=
2x^TPB
\left(
-R^{-1}B^TPx
\right)
$$

por tanto:

$$
\boxed{
2x^TPBu
=
-2x^TPBR^{-1}B^TPx
}
$$

---

## 22.3. Sustitución

Entonces:

$$
0
=
x^TQx
+
x^TPBR^{-1}B^TPx
+
2x^TPAx
-
2x^TPBR^{-1}B^TPx
$$

Agrupando:

$$
\boxed{
0
=
x^TQx
+
2x^TPAx
-
x^TPBR^{-1}B^TPx
}
$$

---

# 23. ¿Por qué puede escribirse $2x^TPAx$ de forma simétrica?

La cantidad:

$$
x^TPAx
$$

es un escalar.

Por tanto:

$$
x^TPAx
=
(x^TPAx)^T
$$

Usando:

$$
(ABC)^T=C^TB^TA^T
$$

tenemos:

$$
(x^TPAx)^T
=
x^TA^TP^Tx
$$

Como:

$$
P=P^T
$$

queda:

$$
x^TPAx
=
x^TA^TPx
$$

Por tanto:

$$
2x^TPAx
=
x^TPAx
+
x^TA^TPx
$$

y:

$$
\boxed{
2x^TPAx
=
x^T(PA+A^TP)x
}
$$

o equivalentemente:

$$
\boxed{
2x^TPAx
=
x^T(A^TP+PA)x
}
$$

> [!IMPORTANT]
> No estamos afirmando que:
>
> $$
> 2PA=A^TP+PA
> $$
>
> como matrices.
>
> La igualdad es válida dentro de la forma cuadrática porque $x^TPAx$ es un escalar.

---

# 24. Ecuación algebraica de Riccati

Volvemos a:

$$
0
=
x^TQx
+
2x^TPAx
-
x^TPBR^{-1}B^TPx
$$

Usando la identidad anterior:

$$
0
=
x^T
\left(
Q
+
PA
+
A^TP
-
PBR^{-1}B^TP
\right)x
$$

Como esto debe cumplirse para cualquier $x$:

$$
\boxed{
A^TP
+
PA
-
PBR^{-1}B^TP
+
Q
=
0
}
$$

Esta es la **ecuación algebraica de Riccati**.

Resolviendo esta ecuación obtenemos la matriz $P$ estabilizante.

Después:

$$
\boxed{
K=R^{-1}B^TP
}
$$

y finalmente:

$$
\boxed{
u=-Kx
}
$$

---

# 25. Regreso a Lyapunov: cerrar el círculo

Habíamos llegado inicialmente a:

$$
\dot V
=
x^T
\left(
A_{cl}^TP+PA_{cl}
\right)x
$$

con:

$$
A_{cl}=A-BK
$$

Queremos comprobar que la $P$ obtenida mediante Riccati hace que esta derivada sea negativa.

---

## 25.1. Expandimos $A_{cl}$

$$
A_{cl}^TP+PA_{cl}
=
(A-BK)^TP
+
P(A-BK)
$$

Entonces:

$$
A_{cl}^TP+PA_{cl}
=
A^TP
-
K^TB^TP
+
PA
-
PBK
$$

o:

$$
\boxed{
A_{cl}^TP+PA_{cl}
=
A^TP+PA
-
K^TB^TP
-
PBK
}
$$

---

## 25.2. Sustituimos Riccati

La ecuación de Riccati:

$$
A^TP+PA-PBR^{-1}B^TP+Q=0
$$

nos permite escribir:

$$
\boxed{
A^TP+PA
=
PBR^{-1}B^TP-Q
}
$$

Por tanto:

$$
A_{cl}^TP+PA_{cl}
=
PBR^{-1}B^TP
-
Q
-
K^TB^TP
-
PBK
$$

---

# 26. ¿Por qué $K^T=PBR^{-1}$?

Tenemos:

$$
\boxed{
K=R^{-1}B^TP
}
$$

Transponemos:

$$
K^T
=
(R^{-1}B^TP)^T
$$

Usando:

$$
(ABC)^T=C^TB^TA^T
$$

obtenemos:

$$
K^T
=
P^T(B^T)^T(R^{-1})^T
$$

Como:

$$
P=P^T
$$

$$
(B^T)^T=B
$$

y, al ser $R$ simétrica,

$$
(R^{-1})^T=R^{-1}
$$

queda:

$$
\boxed{
K^T=PBR^{-1}
}
$$

---

# 27. Continuación de la condición de Lyapunov

Como:

$$
K=R^{-1}B^TP
$$

tenemos:

$$
PBK
=
PBR^{-1}B^TP
$$

y usando:

$$
K^T=PBR^{-1}
$$

también:

$$
K^TB^TP
=
PBR^{-1}B^TP
$$

Entonces:

$$
A_{cl}^TP+PA_{cl}
=
PBR^{-1}B^TP
-
Q
-
PBR^{-1}B^TP
-
PBR^{-1}B^TP
$$

Se cancela uno de los términos positivos con uno de los negativos:

$$
A_{cl}^TP+PA_{cl}
=
-Q
-
PBR^{-1}B^TP
$$

Ahora observamos que:

$$
K^TRK
=
(PBR^{-1})R(R^{-1}B^TP)
$$

por tanto:

$$
\boxed{
K^TRK
=
PBR^{-1}B^TP
}
$$

Finalmente:

$$
\boxed{
A_{cl}^TP+PA_{cl}
=
-(Q+K^TRK)
}
$$

---

# 28. Derivada de Lyapunov bajo el control óptimo

Sustituyendo:

$$
\dot V
=
x^T
\left[
-(Q+K^TRK)
\right]
x
$$

por tanto:

$$
\boxed{
\dot V
=
-x^T(Q+K^TRK)x
}
$$

Como:

$$
u=-Kx
$$

tenemos:

$$
Kx=-u
$$

y:

$$
x^TK^TRKx
=
(Kx)^TR(Kx)
$$

Como el signo desaparece al aparecer cuadráticamente:

$$
(Kx)^TR(Kx)
=
u^TRu
$$

Entonces:

$$
\boxed{
\dot V
=
-\left(
x^TQx+u^TRu
\right)
}
$$

---

# 29. Interpretación de la relación con Bellman

Esta igualdad es especialmente importante:

$$
\boxed{
\dot V
=
-\left(
x^TQx+u^TRu
\right)
}
$$

El término:

$$
x^TQx+u^TRu
$$

es exactamente el **coste instantáneo** que habíamos definido en LQR.

Bellman había escrito:

$$
\boxed{
\text{coste óptimo actual}
=
\text{coste instantáneo durante }dt
+
\text{coste óptimo futuro}
}
$$

En forma diferencial, HJB dice:

$$
\boxed{
0
=
\text{coste instantáneo}
+
\dot V
}
$$

por tanto:

$$
\boxed{
-\dot V
=
\text{coste instantáneo}
}
$$

No es que la parte futura de Bellman desaparezca arbitrariamente.

La función de valor $V(x)$ **ya contiene todo el coste futuro óptimo restante**.

Su disminución:

$$
-\dot V
$$

es precisamente la cantidad de ese coste futuro que estamos "consumiendo" por unidad de tiempo.

---

# 30. Del coste instantáneo al coste total

Partimos de:

$$
\dot V
=
-\left(
x^TQx+u^TRu
\right)
$$

Integramos desde $0$ hasta $\infty$:

$$
\int_0^\infty
\dot V\,dt
=
-
\int_0^\infty
\left(
x^TQx+u^TRu
\right)dt
$$

El lado izquierdo es:

$$
V(\infty)-V(0)
$$

y el lado derecho es:

$$
-J^*
$$

Por tanto:

$$
V(\infty)-V(0)
=
-J^*
$$

Si el sistema converge al origen:

$$
x(t)\to0
$$

entonces:

$$
V(\infty)=0
$$

y obtenemos:

$$
\boxed{
J^*=V(x_0)
}
$$

Como:

$$
V(x)=x^TPx
$$

finalmente:

$$
\boxed{
J^*
=
x_0^TPx_0
}
$$

La matriz $P$ contiene, por tanto, el coste óptimo futuro asociado a cada dirección del espacio de estados.

---

# 31. Qué estamos demostrando realmente

Con este desarrollo hemos demostrado dos cosas distintas.

## 31.1. Estabilidad

La solución estabilizante de Riccati proporciona:

$$
P>0
$$

y:

$$
\dot V
=
-x^T(Q+K^TRK)x
$$

Bajo las condiciones habituales del LQR, esto permite establecer la estabilidad del lazo cerrado.

---

## 31.2. Optimalidad

La HJB nos ha dado:

$$
u^*
=
-R^{-1}B^TPx
$$

es decir:

$$
\boxed{
u^*=-Kx
}
$$

con:

$$
\boxed{
K=R^{-1}B^TP
}
$$

Ese $K$ no es simplemente un $K$ estabilizante.

Es el $K$ que minimiza el coste cuadrático elegido:

$$
\boxed{
J=
\int_0^\infty
\left(
x^TQx+u^TRu
\right)dt
}
$$

---

# 32. Interpretación física de $Q$, $R$, $P$ y $K$

## $Q$

Define qué estados consideramos más importantes.

Un valor grande en $Q_{ii}$ hace que el controlador penalice con fuerza el error del estado $x_i$.

---

## $R$

Penaliza el esfuerzo de control.

Si $R$ aumenta:

- usar control resulta más caro,
- el controlador tiende a ser menos agresivo.

Si $R$ disminuye:

- el esfuerzo de control es más barato,
- el controlador puede actuar de manera más agresiva.

Hay que recordar que:

$$
K=R^{-1}B^TP
$$

aunque $K$ no escala simplemente como $1/R$, porque $P$ también depende de $R$ a través de Riccati.

---

## $P$

Tiene una doble interpretación:

1. **Función de valor óptima**

$$
V(x)=x^TPx
$$

representa el coste mínimo futuro desde el estado $x$.

2. **Función de Lyapunov**

La misma $V=x^TPx$ permite estudiar la estabilidad del sistema en lazo cerrado.

---

## $K$

Es la ganancia de realimentación:

$$
K=
\begin{bmatrix}
k_1&k_2&k_3&k_4
\end{bmatrix}
$$

y el control implementado es:

$$
\boxed{
u
=
-k_1\theta
-k_2\dot\theta
-k_3x
-k_4\dot x
}
$$

---

# 33. La película completa

Ahora sí podemos verla de principio a fin.

$$
\boxed{
\dot x=Ax+Bu
}
$$

↓

**Decidimos realimentar**

$$
\boxed{
u=-Kx
}
$$

↓

Sistema cerrado:

$$
\boxed{
\dot x=(A-BK)x
}
$$

↓

**Lyapunov pregunta:**

$$
\boxed{
\exists P>0:
\quad
A_{cl}^TP+PA_{cl}<0\ ?
}
$$

↓

Pero hay muchos $K$ posibles.

Entonces decimos:

> **No quiero cualquier $K$. Quiero el que minimice $J$.**

↓

Definimos:

$$
\boxed{
J=
\int_0^\infty
(x^TQx+u^TRu)\,dt
}
$$

↓

Bellman:

$$
\boxed{
V(x)=\min J
}
$$

↓

Suponemos:

$$
\boxed{
V=x^TPx
}
$$

↓

HJB:

$$
\boxed{
0=
\min_u
\left[
x^TQx
+
u^TRu
+
\nabla V^T(Ax+Bu)
\right]
}
$$

↓

Minimizamos respecto a $u$:

$$
\boxed{
u^*
=
-R^{-1}B^TPx
}
$$

↓

Por tanto:

$$
\boxed{
K=R^{-1}B^TP
}
$$

↓

Sustituimos en HJB:

$$
\boxed{
A^TP
+
PA
-
PBR^{-1}B^TP
+
Q
=
0
}
$$

↓

Resolvemos Riccati:

$$
\boxed{
P
}
$$

↓

Calculamos:

$$
\boxed{
K=R^{-1}B^TP
}
$$

↓

Aplicamos:

$$
\boxed{
u=-Kx
}
$$

↓

Y entonces:

$$
\boxed{
\dot V
=
-x^T(Q+K^TRK)x
}
$$

↓

Como:

$$
u=-Kx
$$

también:

$$
\boxed{
\dot V
=
-(x^TQx+u^TRu)
}
$$

↓

**Lyapunov demuestra la estabilidad y HJB demuestra la optimalidad respecto al coste elegido.**

---

# 34. La idea que quiero que quede

Hay **dos problemas diferentes** que hemos resuelto consecutivamente.

## Lyapunov

$$
\boxed{
\text{¿Este }K\text{ estabiliza el sistema?}
}
$$

## LQR + HJB

$$
\boxed{
\text{¿Cuál es el }K\text{ que minimiza }J?
}
$$

La maravilla es que **la solución óptima obtenida mediante HJB/Riccati viene acompañada de una función cuadrática que sirve simultáneamente como función de valor y como función de Lyapunov**:

$$
\boxed{
V(x)=x^TPx
}
$$

Por eso el mismo $P$ cumple dos papeles:

$$
\boxed{
P
\Longrightarrow
\begin{cases}
V=x^TPx & \text{función de valor}\\[4pt]
V=x^TPx & \text{función de Lyapunov}
\end{cases}
}
$$

Y finalmente:

$$
\boxed{
Q,R
\longrightarrow
P
\longrightarrow
K
\longrightarrow
u=-Kx
\longrightarrow
\text{estabilidad + coste óptimo}
}
$$

Ese es el recorrido matemático completo del **LQR continuo de horizonte infinito**.

---

# 35. Correcciones importantes respecto a los apuntes manuscritos

> [!WARNING]
> Estas correcciones son importantes para estudiar las ecuaciones sin arrastrar erratas.

### 1. Signo de $K$

En los apuntes aparece en un punto:

$$
K=-R^{-1}B^TP
$$

La expresión correcta es:

$$
\boxed{
K=R^{-1}B^TP
}
$$

porque la ley de control ya contiene el signo negativo:

$$
\boxed{
u=-Kx
}
$$

---

### 2. Condición de Lyapunov

La condición correcta es:

$$
\boxed{
A_{cl}^TP+PA_{cl}<0
}
$$

No:

$$
A_{cl}P+PA_{cl}<0
$$

Falta la traspuesta del primer $A_{cl}$.

---

### 3. $A_{cl}$ no tiene que ser una matriz "negativa"

La condición de estabilidad para:

$$
\dot x=A_{cl}x
$$

es que $A_{cl}$ sea Hurwitz:

$$
\boxed{
\Re\{\lambda_i(A_{cl})\}<0
}
$$

---

### 4. Regla de Bryson para $R$

Para una entrada $u$:

$$
\boxed{
R=\frac{1}{u_{\max}^2}
}
$$

No debe utilizarse $x_{\max}$ en $R$.

---

### 5. Horizonte infinito y coste terminal

En horizonte infinito no es estrictamente necesario pensar "pongo $F=0$".

La formulación habitual simplemente elimina el término terminal finito:

$$
J=
\int_0^\infty
(x^TQx+u^TRu)dt
$$

y busca la solución estacionaria de Riccati.

---

### 6. Convención del factor $\tfrac12$

Es posible definir:

$$
J
=
\frac12
\int_0^\infty
(x^TQx+u^TRu)dt
$$

y:

$$
V=\frac12x^TPx
$$

o bien eliminar ambos factores $\frac12$:

$$
J
=
\int_0^\infty
(x^TQx+u^TRu)dt
$$

$$
V=x^TPx
$$

Ambas convenciones llevan al mismo:

$$
K=R^{-1}B^TP
$$

y a la misma ecuación algebraica de Riccati.

Lo importante es **ser consistente durante toda la deducción**.

---

# 36. Resumen final para repaso rápido

Sistema:

$$
\dot x=Ax+Bu
$$

Realimentación:

$$
u=-Kx
$$

Lazo cerrado:

$$
A_{cl}=A-BK
$$

Lyapunov:

$$
V=x^TPx
$$

$$
\dot V=x^T(A_{cl}^TP+PA_{cl})x
$$

Coste LQR:

$$
J=
\int_0^\infty
(x^TQx+u^TRu)dt
$$

Función de valor:

$$
V(x)=\min J=x^TPx
$$

HJB:

$$
0=
\min_u
[
x^TQx+u^TRu+\nabla V^T(Ax+Bu)
]
$$

Control óptimo:

$$
u^*
=
-R^{-1}B^TPx
$$

Ganancia:

$$
K=R^{-1}B^TP
$$

Riccati:

$$
A^TP+PA-PBR^{-1}B^TP+Q=0
$$

Relación con Lyapunov:

$$
A_{cl}^TP+PA_{cl}
=
-(Q+K^TRK)
$$

Por tanto:

$$
\boxed{
\dot V
=
-(x^TQx+u^TRu)
}
$$

y:

$$
\boxed{
J^*
=
V(x_0)
=
x_0^TPx_0
}
$$
---

# Adéndum — Modelo del péndulo físico con barra + masa acoplada

El modelo original suponía una masa puntual situada a distancia (L) del pivote.

Ahora el péndulo real está compuesto por:

- una barra uniforme de masa (m_b) y longitud (L),
    
- una masa adicional (m_a) acoplada a una distancia (d) del pivote.
    

La masa total es:

$$  
m=m_b+m_a  
$$

y el nuevo centro de masas del conjunto se encuentra a una distancia (l) del pivote:

$$  
\boxed{  
l=  
\frac{  
m_b\frac{L}{2}+m_a d  
}{  
m_b+m_a  
}  
}  
$$

A partir de este punto podemos tratar el movimiento de traslación del conjunto utilizando la posición de su **centro de masas**.

---

# 1. Geometría del nuevo centro de masas

Mantenemos exactamente la misma convención geométrica que en el modelo original:

- (x(t)): posición horizontal del carro.
    
- (\theta(t)): ángulo respecto a la vertical superior.
    
- (l): distancia desde el pivote hasta el centro de masas conjunto.
    

La posición del centro de masas es entonces:

$$  
\boxed{  
x_G=x-l\sin\theta  
}  
$$

$$  
\boxed{  
y_G=l\cos\theta  
}  
$$

La geometría es exactamente la misma que teníamos anteriormente:

$$  
x_p=x-L\sin\theta  
$$

$$  
y_p=L\cos\theta  
$$

pero ahora (L) deja de representar la posición de una masa puntual y utilizamos:

$$  
\boxed{l=\text{distancia al centro de masas real}}  
$$

---

# 2. Velocidad del centro de masas

Partimos de:

$$  
x_G=x-l\sin\theta  
$$

Derivando respecto al tiempo:

# $$  
\dot x_G

\dot x-l\cos\theta\dot\theta  
$$

por tanto:

# $$  
\boxed{  
\dot x_G

\dot x-l\dot\theta\cos\theta  
}  
$$

Para la coordenada vertical:

$$  
y_G=l\cos\theta  
$$

Derivando:

# $$  
\boxed{  
\dot y_G

-l\dot\theta\sin\theta  
}  
$$

---

# 3. Velocidad del centro de masas al cuadrado

El módulo de la velocidad es:

$$  
v_G^2=  
\dot x_G^2+\dot y_G^2  
$$

Sustituyendo:

# $$  
v_G^2 = \left(  
\dot x-l\dot\theta\cos\theta  
\right)^2  
+  
\left(  
-l\dot\theta\sin\theta  
\right)^2  
$$

Desarrollamos:

# $$  
v_G^2 =
 \dot x^2-

2\dot x l\dot\theta\cos\theta  
+  
l^2\dot\theta^2\cos^2\theta  
+  
l^2\dot\theta^2\sin^2\theta  
$$

Utilizando:

$$  
\sin^2\theta+\cos^2\theta=1  
$$

obtenemos:

# $$  
\boxed{  
v_G^2 = \dot x^2-

2\dot x l\dot\theta\cos\theta  
+  
l^2\dot\theta^2  
}  
$$

Hasta aquí, el desarrollo es exactamente análogo al modelo de masa puntual.

---

# 4. Energía cinética

Aquí aparece la diferencia fundamental respecto al modelo original.

Si concentrásemos toda la masa (m) en el centro de masas (G), tendríamos únicamente:

# $$  
T_{\text{tras}}

\frac12m v_G^2  
$$

Sustituyendo (v_G^2):

# $$  
T_{\text{tras}} =

 \frac12m  
\left(  
\dot x^2-

2\dot x l\dot\theta\cos\theta  
+  
l^2\dot\theta^2  
\right)  
$$

es decir:

# $$  
T_{\text{tras}} = \frac12m\dot x^2 -

ml\dot x\dot\theta\cos\theta  
+  
\frac12ml^2\dot\theta^2  
$$

Sin embargo, el péndulo real **no es una masa puntual situada en (G)**.

La barra tiene masa distribuida alrededor de (G), por lo que mientras el centro de masas se desplaza, el cuerpo completo también rota alrededor de su centro de masas.

Esa rotación añade:

# $$  
\boxed{  
T_{\text{rot}} = 

\frac12J_G\dot\theta^2  
}  
$$

donde (J_G) es el momento de inercia del conjunto respecto a su centro de masas.

Por tanto:

$$  
T=T_{\text{tras}}+T_{\text{rot}}  
$$

y obtenemos:

## $$  
T=  
\frac12m\dot x^2-

ml\dot x\dot\theta\cos\theta  
+  
\frac12ml^2\dot\theta^2  
+  
\frac12J_G\dot\theta^2  
$$

Agrupamos los dos últimos términos:

## $$  
T=  
\frac12m\dot x^2-

ml\dot x\dot\theta\cos\theta  
+  
\frac12  
\left(  
ml^2+J_G  
\right)  
\dot\theta^2  
$$

Por el teorema de ejes paralelos:

$$  
J=J_G+ml^2  
$$

donde (J) es el momento de inercia total respecto al pivote.

Por tanto:

## $$  
\boxed{  
T=  
\frac12m\dot x^2-

ml\dot x\dot\theta\cos\theta  
+  
\frac12J\dot\theta^2  
}  
$$
## Añadido — Interpretación de (J = ml^2 + J_G)

Para cualquier cuerpo rígido o conjunto rígido, el momento de inercia respecto al pivote (O) puede expresarse mediante el teorema de ejes paralelos:

$$  
\boxed{  
J_O = ml^2 + J_G  
}  
$$

donde:

- (m) es la masa total del conjunto.
    
- (l) es la distancia desde el pivote (O) hasta el centro de masas (G).
    
- (J_G) es el momento de inercia del conjunto completo respecto a un eje que pasa por su centro de masas (G).
    

El término:

$$  
ml^2  
$$

representa la contribución asociada a desplazar toda la masa total como si estuviera concentrada en (G), mientras que:

$$  
J_G  
$$

representa la contribución adicional debida a que la masa real está distribuida alrededor de ese centro de masas.

### Caso de una barra uniforme

Para una barra uniforme de longitud (L):

$$  
l=\frac L2  
$$

y:

$$  
J_G=\frac1{12}mL^2  
$$

Por tanto:

# $$  
J_O =

m\left(\frac L2\right)^2  
+  
\frac1{12}mL^2  
$$

# $$  
J_O =

\frac14mL^2+\frac1{12}mL^2  
$$

$$  
\boxed{  
J_O=\frac13mL^2  
}  
$$

En este caso existe una expresión teórica conocida para la barra respecto a uno de sus extremos, por lo que puede utilizarse directamente:

$$  
\boxed{  
J_O=\frac13mL^2  
}  
$$

### Caso de barra + masa acoplada

Para el sistema real formado por una barra y una masa puntual acoplada, el nuevo centro de masas ya no se encuentra necesariamente en (L/2).

Su posición es:

$$  
\boxed{  
l=  
\frac{  
m_bL/2+m_ad  
}{  
m_b+m_a  
}  
}  
$$

Conceptualmente, el momento de inercia total podría seguir escribiéndose como:

$$  
\boxed{  
J_O=m_{\text{total}}l^2+J_G  
}  
$$

donde ahora (J_G) representa la distribución de masa de **todo el conjunto** respecto a su nuevo centro de masas.

Sin embargo, resulta más sencillo calcular directamente el momento de inercia de cada componente respecto al pivote:

$$  
J_{\text{barra}}=\frac13m_bL^2  
$$

$$  
J_{\text{masa}}=m_ad^2  
$$

y sumarlos:

$$  
\boxed{  
J_O=  
\frac13m_bL^2+m_ad^2  
}  
$$

Ambas expresiones son equivalentes:

# $$  
\boxed{  
m_{\text{total}}l^2+J_G =

\frac13m_bL^2+m_ad^2  
}  
$$

Por tanto, en el desarrollo del modelo puede utilizarse directamente:

$$  
\boxed{  
J=  
\frac13m_bL^2+m_ad^2  
}  
$$

sin necesidad de calcular explícitamente (J_G).

> [!NOTE]  
> El nuevo centro de masas (l) y el momento de inercia (J) contienen información diferente.
> 
> (l) indica **dónde está concentrada, en promedio, la masa del sistema**, mientras que (J) indica **cómo está distribuida esa masa respecto al pivote**.
> 
> Por ello, conocer únicamente (l) no es suficiente para determinar la dinámica angular del péndulo.

---

## ¿Dónde queda entonces el (1/3) de la barra?

Queda contenido dentro de (J).

Para nuestro sistema:

$$  
\boxed{  
J=  
\frac13m_bL^2+m_a d^2  
}  
$$

Por tanto, realmente la energía cinética es:
## $$  
\boxed{  
T=  
\frac12m\dot x^2-

ml\dot x\dot\theta\cos\theta  
+  
\frac12J\dot\theta^2  
}  
$$
## $$  
\boxed{  
T=  
\frac12(m_b+m_a)\dot x^2

-(m_b+m_a)l\dot x\dot\theta\cos\theta  
+  
\frac12  
\left(  
\frac13m_bL^2+m_a d^2  
\right)  
\dot\theta^2  
}  
$$

> [!IMPORTANT]
> En el modelo original no aparece explícitamente el momento de inercia propio del péndulo porque este se modeló como una **masa puntual \(m\) situada a distancia \(L\) del pivote y unida mediante una barra ideal sin masa**.
>
> Para una masa puntual, el momento de inercia respecto a su propio centro de masas es:
>
> $$
> J_G=0
> $$
>
> ya que, por definición, no existe una distribución espacial de masa alrededor de \(G\).
>
> Por ello, toda su energía cinética puede obtenerse directamente a partir del movimiento de la masa puntual:
>
> $$
> T=\frac12mv^2
> $$
>
> Como la masa puntual se encuentra a una distancia \(L\) del pivote, su velocidad tangencial debida al giro es:
>
> $$
> v=L\dot\theta
> $$
>
> y aparece:
>
> $$
> T=\frac12mL^2\dot\theta^2
> $$
>
> Por tanto, aunque en el modelo original no se introdujera explícitamente un momento de inercia, este estaba implícito como:
>
> $$
> \boxed{
> J_O=mL^2
> }
> $$
>
> ---
>
> En el sistema real, sin embargo, la barra posee una masa \(m_b\) no despreciable.
>
> El péndulo deja entonces de ser:
>
> $$
> \text{barra ideal sin masa + masa puntual}
> $$
>
> y pasa a ser:
>
> $$
> \text{barra con masa distribuida + masa acoplada}
> $$
>
> Ambas modificaciones deben incorporarse al nuevo modelo dinámico.

---

# 5. Energía potencial

La gravedad puede considerarse aplicada en el centro de masas total.

Como:

$$  
y_G=l\cos\theta  
$$

la energía potencial es:

$$  
V=mgy_G  
$$

por tanto:

$$  
\boxed{  
V=mgl\cos\theta  
}  
$$

---

# 6. Lagrangiano

El Lagrangiano es:

$$  
\mathcal L=T-V  
$$

por tanto:

# $$  
\boxed{  
\mathcal L =  \frac12m\dot x^2

- ml\dot x\dot\theta\cos\theta  
+  
\frac12J\dot\theta^2

mgl\cos\theta  
}  
$$

---

# 7. Euler-Lagrange para (\theta)

Aplicamos:

## $$  
\frac{d}{dt}  
\left(  
\frac{\partial\mathcal L}  
{\partial\dot\theta}  
\right)

\frac{\partial\mathcal L}  
{\partial\theta}  
=0  
$$

Partimos de:

# $$  
\mathcal L=

\frac12m\dot x^2

- ml\dot x\dot\theta\cos\theta  
+  
\frac12J\dot\theta^2

mgl\cos\theta  
$$

## 7.1. Derivada respecto a (\dot\theta)

# $$  
\frac{\partial\mathcal L}  
{\partial\dot\theta}=

-ml\dot x\cos\theta  
+  
J\dot\theta  
$$

Derivando respecto al tiempo:

# $$  
\frac{d}{dt}  
\left(  
\frac{\partial\mathcal L}  
{\partial\dot\theta}  
\right)=

-ml\ddot x\cos\theta  
+  
ml\dot x\dot\theta\sin\theta  
+  
J\ddot\theta  
$$

---

## 7.2. Derivada respecto a (\theta)

Los términos que dependen de (\theta) son:

## $$  
-ml\dot x\dot\theta\cos\theta

-mgl\cos\theta  
$$

por tanto:

# $$  
\frac{\partial\mathcal L}  
{\partial\theta}=

ml\dot x\dot\theta\sin\theta  
+  
mgl\sin\theta  
$$

---

# 8. Ecuación dinámica no lineal

Sustituyendo en Euler-Lagrange:

## $$  
-ml\ddot x\cos\theta  
+  
ml\dot x\dot\theta\sin\theta  
+  
J\ddot\theta

-ml\dot x\dot\theta\sin\theta

- mgl\sin\theta

=0  
$$

Los términos cruzados se cancelan:

## $$  
ml\dot x\dot\theta\sin\theta-

ml\dot x\dot\theta\sin\theta  
=0  
$$

queda:

## $$  
\boxed{  
-ml\ddot x\cos\theta  
+  
J\ddot\theta

- mgl\sin\theta

=0  
}  
$$

Despejando:

# $$  
\boxed{  
\ddot\theta=

\frac{ml}{J}\ddot x\cos\theta  
+  
\frac{mgl}{J}\sin\theta  
}  
$$

Esta sustituye a la ecuación obtenida para la masa puntual:

# $$  
\ddot\theta=

\frac{\ddot x}{L}\cos\theta  
+  
\frac{g}{L}\sin\theta  
$$

---

# 9. Linealización alrededor de la vertical superior

Para:

$$  
\theta\approx0  
$$

utilizamos:

$$  
\sin\theta\approx\theta  
$$

y:

$$  
\cos\theta\approx1  
$$

por tanto:

# $$  
\boxed{  
\ddot\theta

\frac{mgl}{J}\theta  
+  
\frac{ml}{J}\ddot x  
}  
$$

Definiendo:

$$  
u=\ddot x  
$$

obtenemos:

# $$  
\boxed{  
\ddot\theta=

\frac{mgl}{J}\theta  
+  
\frac{ml}{J}u  
}  
$$

---

# 10. Modelo en espacio de estados

Manteniendo:

# $$  
\mathbf{x}=

\begin{bmatrix}  
\theta\\ 
\dot\theta\\  
x\\
\dot x\\  
\end{bmatrix}  
$$

tenemos:

$$  
\boxed{  
A=  
\begin{bmatrix}  
0&1&0&0\\  
\frac{mgl}{J}&0&0&0\\  
0&0&0&1\\ 
0&0&0&0\\  
\end{bmatrix}  
}  
$$

y:

$$  
\boxed{  
B=  
\begin{bmatrix}  
0\\  
\frac{ml}{J}\\  
0\\  
1  
\end{bmatrix}  
}  
$$

con:

$$  
m=m_b+m_a  
$$

$$  
l=  
\frac{  
m_bL/2+m_a d  
}{  
m_b+m_a  
}  
$$

$$  
J=  
\frac13m_bL^2+m_a d^2  
$$

---

> [!IMPORTANT]  
> El nuevo centro de masas (l) permite escribir la geometría exactamente igual que en el modelo original:
> 
> $$  
> x_G=x-l\sin\theta  
> $$
> 
> $$  
> y_G=l\cos\theta  
> $$
> 
> pero **no podemos sustituir simplemente (L\rightarrow l) en todo el modelo original**.
> 
> Hacerlo implicaría asumir que toda la masa está concentrada en (G), es decir:
> 
> $$  
> J=ml^2  
> $$
> 
> cuando para la barra + masa acoplada realmente:
> 
> $$  
> J=\frac13m_bL^2+m_a d^2  
> $$
> 
> Por eso las coordenadas dependen únicamente del nuevo centro de masas (l), mientras que la dinámica angular necesita además el momento de inercia (J).