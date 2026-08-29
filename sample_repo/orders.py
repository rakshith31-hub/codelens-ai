def calculate_discount(price, is_member):
    if is_member:
        return price * 0.9
    return price


def calculate_tax(price):
    return price * 0.18


def calculate_total(price, is_member):
    discounted = calculate_discount(price, is_member)
    tax = calculate_tax(discounted)
    return discounted + tax


def apply_coupon(total, coupon_code):
    if coupon_code == "SAVE10":
        return total - 10
    return total


def checkout(price, is_member, coupon_code=None):
    total = calculate_total(price, is_member)
    if coupon_code:
        total = apply_coupon(total, coupon_code)
    return round(total, 2)
