class XGCD:
    """
    A gcd co-processor unit.
    """

    @staticmethod
    def compute(a: int, b: int) -> tuple[int, int, int]:
        """
        Extended Euclidean Algorithm without recursion.
        Computes integers x and y such that ax + by = gcd(a, b).

        Parameters:
            a (int): The first integer.
            b (int): The second integer.

        Returns:
            tuple[int, int, int]: A tuple containing (gcd, x, y),
            where gcd is the greatest common divisor of a and b,
            and x, y satisfy the equation ax + by = gcd.

        Example:
            >>> XGCD.compute(240, 46)
            (2, -9, 47)
        """
        x0, x1 = 1, 0
        y0, y1 = 0, 1

        while b != 0:
            q = a // b
            a, b = b, a % b
            x0, x1 = x1, x0 - q * x1
            y0, y1 = y1, y0 - q * y1

        gcd = a if a >= 0 else -a
        return gcd, x0, y0

    @staticmethod
    def gcd(a: int, b: int) -> int:
        """
        Computes the greatest common divisor of a and b using the compute method.

        Parameters:
            a (int): The first integer.
            b (int): The second integer.

        Returns:
            int: The greatest common divisor of a and b.

        Example:
            >>> XGCD.gcd(240, 46)
            2
        """
        gcd_value, _, _ = XGCD.compute(a, b)
        return gcd_value

    @staticmethod
    def modinv(a: int, m: int) -> int:
        """
        Computes the modular inverse of a modulo m using the compute method.
        Finds x such that (a * x) % m == 1.

        Parameters:
            a (int): The integer whose modular inverse is to be computed.
            m (int): The modulus.

        Returns:
            int: The modular inverse of a modulo m.

        Raises:
            ValueError: If the modular inverse does not exist.

        Example:
            >>> XGCD.modinv(3, 11)
            4
        """
        gcd_value, x, _ = XGCD.compute(a, m)
        if gcd_value != 1:
            raise ValueError(f"Modular inverse does not exist because gcd({a}, {m}) = {gcd_value} ≠ 1")
        else:
            return x % m

    @staticmethod
    def solve_linear_diophantine(a: int, b: int, c: int) -> tuple[int, int]:
        """
        Solves the linear Diophantine equation a * x + b * y = c using the compute method.

        Parameters:
            a (int): Coefficient of x.
            b (int): Coefficient of y.
            c (int): Right-hand side constant.

        Returns:
            tuple[int, int]: A particular solution (x0, y0) to the equation.

        Raises:
            ValueError: If no integer solutions exist.

        Example:
            >>> XGCD.solve_linear_diophantine(15, 25, 5)
            (2, -1)
        """
        gcd_value, x0, y0 = XGCD.compute(a, b)
        if c % gcd_value != 0:
            raise ValueError(f"No integer solutions because gcd({a}, {b}) = {gcd_value} does not divide {c}")
        else:
            factor = c // gcd_value
            return x0 * factor, y0 * factor

    @staticmethod
    def lcm(a: int, b: int) -> int:
        """
        Computes the least common multiple of a and b using the gcd method.

        Parameters:
            a (int): The first integer.
            b (int): The second integer.

        Returns:
            int: The least common multiple of a and b.

        Example:
            >>> XGCD.lcm(12, 18)
            36
        """
        gcd_value = XGCD.gcd(a, b)
        return abs(a * b) // gcd_value if gcd_value != 0 else 0

    @staticmethod
    def is_coprime(a: int, b: int) -> bool:
        """
        Checks if two integers are coprime using the gcd method.

        Parameters:
            a (int): The first integer.
            b (int): The second integer.

        Returns:
            bool: True if a and b are coprime, False otherwise.

        Example:
            >>> XGCD.is_coprime(14, 15)
            True
        """
        return XGCD.gcd(a, b) == 1

# if __name__ == '__main__':
#     a, b = 240, 46
#     gcd_value, x, y = XGCD.compute(a, b)
#     print(f"gcd({a}, {b}) = {gcd_value}")
#     print(f"Coefficients x = {x}, y = {y}")
#     print(f"Verification: {a}*({x}) + {b}*({y}) = {a * x + b * y}")