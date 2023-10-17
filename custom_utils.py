def find_ring_intersection(start_point, circle_center, circle_radius):
    start_x, start_y = start_point
    center_x, center_y = circle_center

    # Calculate the slope of the line
    slope = (center_y - start_y) / (center_x - start_x)

    # Coefficients for the quadratic equation
    coeff_a = 1 + slope**2
    coeff_b = 2*slope*(start_y - center_y) - 2*center_x
    coeff_c = center_x**2 + (start_y - center_y)**2 - circle_radius**2

    # Solve the quadratic equation
    discriminant = coeff_b**2 - 4*coeff_a*coeff_c
    if discriminant < 0:
        return None  # No intersection

    intersection_x1 = (-coeff_b + discriminant**0.5) / (2*coeff_a)
    intersection_y1 = slope*(intersection_x1 - start_x) + start_y

    intersection_x2 = (-coeff_b - discriminant**0.5) / (2*coeff_a)
    intersection_y2 = slope*(intersection_x2 - start_x) + start_y

    # Return the intersection point closer to start_point
    if (intersection_x1 - start_x)**2 + (intersection_y1 - start_y)**2 < (intersection_x2 - start_x)**2 + (intersection_y2 - start_y)**2:
        return (intersection_x1, intersection_y1)
    else:
        return (intersection_x2, intersection_y2)


class EventListener:
    def __init__(self, value=None, bind=None):
        self._value = value

        if bind is not None:
            assert callable(bind), "The provided bind argument must be callable"
            self._bindings = [bind, ]
        else:
            self._bindings = []

    def __call__(self, value):
        self.value = value
        return self.value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value == self._value:
            return

        self._value = value
        for binding in self._bindings:
            binding(value)

    def bind(self, bind):
        assert callable(bind)
        self._bindings.append(bind)

    def unbind(self, bind):
        self._bindings.remove(bind)

    def bindings(self):
        return self._bindings
