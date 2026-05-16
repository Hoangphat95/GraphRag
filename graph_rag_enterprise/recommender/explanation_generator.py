class ExplanationGenerator:

    def generate(self, tire, reasons):
        explain = f"Lốp {tire.get('size')} ({tire.get('brand')}) được chọn vì:\n"

        for r in reasons:
            explain += f"✔ {r}\n"

        return explain