import simpy
import random

total_mins = 720

#One person comes every 4 minutes duing prime hours
mean_arrival_regular = 4
std_arrival_regular = 1

#One person comes every one minutes druign prime hours
mean_arrival_prime = 1
std_arrival_prime = 0.2

class clarks:
    def __init__(self, env):
       self.env = env
       # Start the run process everytime an instance is created.
       self.action = env.process(self.run(env))
       self.shop = simpy.Container(env, capacity = 10, init = 0) # No more new customers after enough people are in shop
       self.line = simpy.Container(env, capacity = 15, init = 0) #No more new customers after 20 in shop
       self.food_line = simpy.Container(env, capacity = 5, init = 0)
       self.dispatch = simpy.Container(env, capacity = 10000, init = 0)
       self.lost = simpy.Container(env, capacity = 10000, init = 0)
       self.lost_food = simpy.Container(env, capacity = 10000, init = 0)
       self.line_control = env.process(self.line_level(env))
       self.shop_control = env.process(self.shop_level(env))

    def line_level(self, env):
        yield env.timeout(0)
        control_list = [0]
        while True:
            if control_list[-1] == 0:
                if self.line.level == 15:
                    control_list.append(1)
                    #print("line full capacity {} {}".format(env.now, self.line.level))
                    count_line.append(1)
                    yield env.timeout(1)
                    
            elif control_list[-1] == 1:
                if self.line.level < 15:
                    control_list.append(0)
                    #print("line regular capacity {} {}".format(env.now, self.line.level))
                    yield env.timeout(1)
            yield env.timeout(1)  

    def shop_level(self, env):
        yield env.timeout(0)
        control_list = [0]
        while True:
            if control_list[-1] == 0:
                if self.shop.level == 10:
                    control_list.append(1)
                    #print("shop full capacity {} {}".format(env.now, self.shop.level))
                    count_shop.append(1)
                    yield env.timeout(1)
                    
            elif control_list[-1] == 1:
                if self.shop.level < 10:
                    control_list.append(0)
                    #print("shop normal capacity {} {}".format(env.now, self.shop.level))
                    yield env.timeout(1)
            yield env.timeout(1)  

    def run(self, env):
        while True:            
            if env.now <= 60:
                yield self.env.process(self.deli_regular(env))

            elif env.now > 60 and env.now <= 120:
                yield self.env.process(self.deli_prime(env))

            elif env.now > 120 and env.now <= 300:
                yield self.env.process(self.deli_regular(env))

            elif env.now > 300 and env.now <= 360:
                yield self.env.process(self.deli_prime(env))

            elif env.now > 360 and env.now <= 540:
                yield self.env.process(self.deli_regular(env))

            elif env.now > 540 and env.now <= 600:
                yield self.env.process(self.deli_prime(env))
   
            elif env.now > 600 and env.now <= 720:
                yield self.env.process(self.deli_regular(env))
              
    def deli_regular(self, env):
        arrival_time = random.gauss(mean_arrival_regular, std_arrival_regular)
        yield env.timeout(arrival_time)
        if random.random() <= 0.8:
            count_regular.append(1)
            if self.shop.level == self.shop.capacity:
                yield self.lost.put(1)
            else:
                yield self.shop.put(1)
        else:
            count_food.append(1)
            if self.food_line.level == self.food_line.capacity:
                yield self.lost_food.put(1)  
            else:
                yield self.food_line.put(1)
            
          
    def deli_prime(self, env):
        arrival_time = random.gauss(mean_arrival_prime, std_arrival_prime)
        yield env.timeout(arrival_time)
        if random.random() <= 0.8:
            count_prime.append(1)
            if self.shop.level == self.shop.capacity:
                yield self.lost.put(1)  
            else:
                yield self.shop.put(1)
        else:
            count_food.append(1)
            if self.food_line.level == self.food_line.capacity:
                yield self.lost_food.put(1)  
            else:
                yield self.food_line.put(1)

#-----------------------------------------------------------------------------
def food_court(env, clarks):
    while True:
        yield clarks.food_line.get(1)
        stay_time = random.gauss(mean_food_line, std_food_line)
        yield env.timeout(stay_time)
        if clarks.line.level == clarks.line.capacity:
            yield clarks.lost_food.put(1)  
        else:
            yield clarks.line.put(2)
            #person in charge has to manually input stuff in order so twice as costly
            #Food court person also typically spends 10 as opposed to 5

def deli_stay(env, clarks):
    while True:
        yield clarks.shop.get(1)
        stay_time = random.gauss(mean_stay, std_stay)
        yield env.timeout(stay_time)
        if clarks.line.level == clarks.line.capacity:
            yield clarks.lost.put(1)  
        else:
            yield clarks.line.put(1)

def deli_checkout(env, clarks):
    while True:
        yield clarks.line.get(1)
        checkout_time = random.gauss(mean_checkout, std_checkout)
        yield env.timeout(checkout_time)
        yield clarks.dispatch.put(1)

def employee(env, clarks):
    while True:
        yield clarks.line.get(1)
        checkout_time = random.gauss(mean_checkout*1.5, std_checkout*1.5)
        yield env.timeout(checkout_time)
        yield clarks.dispatch.put(1)

def checkout(env, clarks):
    for i in range(0):
        env.process(employee(env, clarks))
        yield env.timeout(0)

#-----------------------------------------------------------------------------
env = simpy.Environment()

clarks = clarks(env)

#A person stays in the shop for about 3 minutes
mean_stay = 3 + 0.2*clarks.line.level
std_stay = 0.25

#It takes about 3 minutes for a person to checkout and pay
mean_checkout = 3
std_checkout = 0.2

# A person stays in the food line for about 5 minutes
mean_food_line = 5
std_food_line = 0.5

count_food = []

count_prime = []

count_regular = []

count_shop = []

count_line = []

deli_stay = env.process(deli_stay(env, clarks))

deli_checkout = env.process(deli_checkout(env, clarks))
        
employee_checkout = env.process(checkout(env, clarks))

deli_food_court = env.process(food_court(env, clarks))

env.run(until=total_mins)

mean_rev_per_head = 5
std_rev_per_head = 1.5

Revenue = (clarks.dispatch.level * random.gauss(mean_rev_per_head, std_rev_per_head) + clarks.line.level * random.gauss(mean_rev_per_head, std_rev_per_head)
           + clarks.shop.level * random.gauss(mean_rev_per_head, std_rev_per_head))# - 121
#adjust this to a normal distribution

Revenue_lost = clarks.lost.level * random.gauss(mean_rev_per_head, std_rev_per_head) + clarks.lost_food.level * random.gauss(mean_rev_per_head, std_rev_per_head) *2
#Adjust this to a normal distribution

f = open("base_record.txt", "a")
f.write("{}, {}, {}, {} \n".format(round(Revenue), round(Revenue_lost), sum(count_shop), sum(count_line)))
f.close()

print(sum(count_shop))#Number of times max number in shop was reached
print(sum(count_line))#Number of times max number in line was reached
print(sum(count_regular))#Number of regular customers that entered
print(sum(count_prime))#Number of prime customers that entered
print(sum(count_food))#Number of food customers that entered

print("________")
print("{0} people in line".format(clarks.line.level))
print("{0} people in shop".format(clarks.shop.level))
print("{0} people in food".format(clarks.food_line.level))
print("{0} people were dispatched".format(clarks.dispatch.level))
print("{0} customers were lost".format(clarks.lost.level))
print("{0} food people were lost".format(clarks.lost_food.level))
print("{0} money was made".format(round(Revenue)))
print("{0} money was lost".format(round(Revenue_lost)))

#Notes
#Line control seems to be working properly
#Shop capacity seems to be working properly
#three tasks
#Getting a second till
#Getting rid of the food counter and expanding the line limit to 15
#Putting customers outside in the rain and observing how that effects the line

