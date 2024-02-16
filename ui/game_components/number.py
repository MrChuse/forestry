from typing import List
from itertools import product

init = '''90342 2
70794 0
39458 2
34109 1
51545 2
12531 1'''
a = init.split('\n')
constraints = [el.split() for el in a]
constraints = [(el[0], int(el[1])) for el in constraints]
constraints.sort(key=lambda x:x[1])
possible_digits = [{el for el in '0123456789'} for _ in range(len(constraints))]

# print(nums_corrects, possible_digits)

def print_p(possible_digits):
    num = 1
    for pd in possible_digits:
        num *= len(pd)
    if num > 100:
        print(possible_digits)
    else:
        p = product(*possible_digits)
        print('\n'.join(sorted(''.join(el) for el in p)))


def apply_constraint(possible_digits: List[set], constraint):
    cons_digits, amount = constraint
    if amount == 0:
        new_possible_digits = []
        for possible_digit, cons_digit in zip(possible_digits, cons_digits):
            new_possible_digit = possible_digit.copy()
            new_possible_digit.remove(cons_digit)
            new_possible_digits.append(new_possible_digit)
        return [new_possible_digits]
    elif amount == 1:
        possible_digits_list = []
        for correct_place in range(len(cons_digits)):
            possible = True
            new_possible_digits = []
            for index, (possible_digit, cons_digit) in enumerate(zip(possible_digits, cons_digits)):
                new_possible_digit = possible_digit.copy()
                # print(correct_place, index, possible_digit, cons_digit)
                if index == correct_place:
                    if cons_digit in new_possible_digit:
                        new_possible_digit = {cons_digit}
                        # print('same, new_digit:', new_possible_digit)
                    else:
                        possible = False
                        print('1 impossbile, digit was removed but it is the correct one')
                else:
                    if cons_digit in new_possible_digit:
                        new_possible_digit.remove(cons_digit)
                    if len(new_possible_digit) == 0:
                        possible = False
                        print('1 impossible, this digit has no possible digits')
                    # else:
                        # print('not same, removed:', new_possible_digit)
                new_possible_digits.append(new_possible_digit)
            if possible:
                possible_digits_list.append(new_possible_digits)
                # print('was possible, new list', possible_digits_list)
            # else:
                # print('wasnt possible')
        return possible_digits_list
    elif amount == 2:
        possible_digits_list = []
        for correct_place1 in range(len(cons_digits)-1):
            for correct_place2 in range(correct_place1+1, len(cons_digits)):
                possible = True
                new_possible_digits = []
                for index, (possible_digit, cons_digit) in enumerate(zip(possible_digits, cons_digits)):
                    new_possible_digit = possible_digit.copy()
                    print(correct_place1, correct_place2, index, possible_digit, cons_digit)
                    if index == correct_place1 or index == correct_place2:
                        if cons_digit in new_possible_digit:
                            new_possible_digit = {cons_digit}
                            # print('same, new_digit:', new_possible_digit)
                        else:
                            possible = False
                            print('2 impossbile, digit was removed but it is the correct one')
                    else:
                        if cons_digit in new_possible_digit:
                            new_possible_digit.remove(cons_digit)
                        if len(new_possible_digit) == 0:
                            print('2 impossible, this digit has no possible digits')
                            possible = False
                        # else:
                            # print('not same, removed:', new_possible_digit)
                    new_possible_digits.append(new_possible_digit)
                if possible:
                    possible_digits_list.append(new_possible_digits)
                    # print('was possible, new list', possible_digits_list)
                # else:
                    # print('wasnt possible')
            return possible_digits_list
        #         print(correct_place1, correct_place2)
        # return [possible_digits]


# mock_pd = [{'1', '2', '3'}, {'1','2','3'}, {'1','2','3'}]

def apply_constraints(start, constraints):
    possible_digits = [start]
    for c in constraints:
        new_possible_digits = []
        for pd in possible_digits:
            new_possible_digits.extend(apply_constraint(pd, c))
            # print('used', pd)
        possible_digits = new_possible_digits
        print('applied', c, len(possible_digits))
    return possible_digits

possible_digits = apply_constraints(possible_digits, constraints)
for pd in possible_digits:
    print_p(pd)
    print()

# mock_pd_list = apply_constraint(mock_pd, ('333', 0))
# for mpd in mock_pd_list:
#     print_p(mpd)
#     print()
# print_p()
# print_p(possible_digits)
