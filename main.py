from ringresonator_study import AddDropRing, Coupler


def main():
    # Field-amplitude coefficients. For this example each coupler is lossless:
    # abs(t)**2 + abs(kappa)**2 = 1.
    ring = AddDropRing(
        input_coupler=Coupler(t=0.95, kappa=1j * (1 - 0.95**2) ** 0.5),
        output_coupler=Coupler(t=0.95, kappa=1j * (1 - 0.95**2) ** 0.5),
        alpha=0.98,
    )

    response = ring.response(phi=0.0)
    for port, value in response.items():
        print(
            f"{port}: amplitude={value.amplitude:.6g}, "
            f"power={value.power:.6g}, phase={value.phase:.6g} rad"
        )


if __name__ == "__main__":
    main()
