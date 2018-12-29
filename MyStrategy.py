
import math
from pprint import pprint

tick_cnt = 0

##########################################################################################################
class Consts:
    EPS = f64 = 1e-5
    # Константы, взятые из документации
    BALL_RADIUS = 2.0
    ROBOT_MAX_RADIUS = 1.05
    MAX_ENTITY_SPEED = 100.0
    ROBOT_MAX_GROUND_SPEED = 30.0
    ROBOT_MAX_JUMP_SPEED = 15.0

    JUMP_TIME = 0.2
    MAX_JUMP_HEIGHT = 3.0 

##########################################################################################################
class Vec2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def len(self) -> float:
        """
        Нахождение длины вектора
        """

        return math.sqrt(self.x * self.x + self.y * self.y)


    
    def normalize(self) -> "Vec2":
        """
        Нормализация вектора (приведение длины к 1)
        """
        return self * (1.0 / self.len())

    # ===================================================
    def __sub__(self, b: "Vec2") -> "Vec2":
        return Vec2(self.x - b.x, self.y - b.y)

    def __add__(self, b: "Vec2") -> "Vec2":
        return Vec2(self.x + b.x, self.y + b.y)

    def __mul__(self, k: float) -> "Vec2":
        return Vec2(self.x * k, self.y * k)           

    # ===================================================
    def position(obj) -> "Vec2":
        return Vec2(obj.x, obj.z)
        
    def velocity(obj) -> "Vec2":
        return Vec2(obj.velocity_x, obj.velocity_z)      


##########################################################################################################
class MyStrategy:
    def act(self, me, rules, game, action):
        global tick_cnt
        tick_cnt += 1
        print(f"------- New tick starts {tick_cnt} -----------")
        print("Me.Id", me.id)
        print(f"ME(x,y,z) = {me.x}, {me.y}, {me.z}")
        print(f"BALL(x,y,z) = {game.ball.x}, {game.ball.y}, {game.ball.z}")


        # Наша стратегия умеет играть только на земле
        # Поэтому, если мы не касаемся земли, будет использовать нитро
        # чтобы как можно быстрее попасть обратно на землю
        if not me.touch:
            print("DBG: Return to the ground")
            action.target_velocity_x = 0.0
            action.target_velocity_y = - Consts.MAX_ENTITY_SPEED
            action.target_velocity_z = 0.0
            action.jump_speed =  0.0
            action.use_nitro = True
            return


        # Если при прыжке произойдет столкновение с мячом, и мы находимся
        # с той же стороны от мяча, что и наши ворота, прыгнем, тем самым
        # ударив по мячу сильнее в сторону противника
        dist = math.sqrt (
            math.pow(me.x - game.ball.x, 2)
            + math.pow(me.y - game.ball.y, 2)
            + math.pow(me.z - game.ball.z, 2)
        )

        jump = dist < Consts.BALL_RADIUS + Consts.ROBOT_MAX_RADIUS and me.z < game.ball.z
        print("is_jump", jump)

        # Так как роботов несколько, определим нашу роль - защитник, или нападающий
        # Нападающим будем в том случае, если есть дружественный робот,
        # находящийся ближе к нашим воротам
        is_attacker = len(game.robots) == 2
        
        for robot in game.robots:
            if robot.is_teammate and robot.id != me.id:
                if Vec2.position(robot).y < Vec2.position(me).y:
                    print("DBG: closer is_attacker = True")
                    is_attacker = True


        if is_attacker:
            print("DBG: Attacker strategy")
            # Стратегия нападающего:
            # Просимулируем примерное положение мяча в следующие 10 секунд, с точностью 0.1 секунды
            for i in range(1, 100):
                t = i * 0.1
                ball_pos = Vec2.position(game.ball) + Vec2.velocity(game.ball) * t
                # Если мяч не вылетит за пределы арены
                # (произойдет столкновение со стеной, которое мы не рассматриваем),
                # и при этом мяч будет находится ближе к вражеским воротам, чем робот,
                if ball_pos.y > Vec2.position(me).y and abs(ball_pos.x) < (rules.arena.width / 2.0) and abs(ball_pos.y) < (rules.arena.depth / 2.0):
                    # Посчитаем, с какой скоростью робот должен бежать,
                    # Чтобы прийти туда же, где будет мяч, в то же самое время
                    delta_pos = Vec2(ball_pos.x, ball_pos.y) - Vec2(Vec2.position(me).x, Vec2.position(me).y)
                    need_speed = delta_pos.len() / t
                    # Если эта скорость лежит в допустимом отрезке
                    if 0.5 * Consts.ROBOT_MAX_GROUND_SPEED < need_speed and need_speed < Consts.ROBOT_MAX_GROUND_SPEED:
                        # То это и будет наше текущее действие
                        target_velocity = Vec2(delta_pos.x, delta_pos.y).normalize() * need_speed;
                        action.target_velocity_x = target_velocity.x
                        action.target_velocity_y = 0.0
                        action.target_velocity_z = target_velocity.y
                        action.jump_speed = Consts.ROBOT_MAX_JUMP_SPEED if jump else  0.0 
                        action.use_nitro =  False
                        return
            print("DBG: Attacker  strategy END")

        print("DBG: Defender strategy")
        # Стратегия защитника (или атакующего, не нашедшего хорошего момента для удара):
        # Будем стоять посередине наших ворот
        target_pos = Vec2(0.0, -(rules.arena.depth / 2.0) + rules.arena.bottom_radius)
        # Причем, если мяч движется в сторону наших ворот
        if Vec2.velocity(game.ball).y < -Consts.EPS:
            # Найдем время и место, в котором мяч пересечет линию ворот
            t = (target_pos.y - Vec2.position(game.ball).y) / Vec2.velocit-y(game.ball).y
            x = Vec2.position(game.ball).x + Vec2.velocity(game.ball).x * t
            # Если это место - внутри ворот
            if abs(x) < (rules.arena.goal_width / 2.0):
                # То пойдем защищать его
                target_pos.x = x
            
        

        # Установка нужных полей для желаемого действия
        target_velocity = Vec2(
            target_pos.x - Vec2.position(me).x,
            target_pos.y - Vec2.position(me).y,
        ) * Consts.ROBOT_MAX_GROUND_SPEED
        
        action.target_velocity_x = target_velocity.x
        action.target_velocity_y = 0.0
        action.target_velocity_z = target_velocity.y
        action.jump_speed = Consts.ROBOT_MAX_JUMP_SPEED if jump else 0.0
        action.use_nitro = False
        print("DBG: method ends")