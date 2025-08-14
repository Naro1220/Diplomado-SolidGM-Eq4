import argparse
from test_manager.test_manager import TestManager

def main():
    parser = argparse.ArgumentParser(description="Execute test case")
    parser.add_argument(
        "serial_number",
        type=str,
        help="SSD's serial number to test"
    )
    parser.add_argument(
        "testname",
        type=str,
        help="Testname"
    )

    args = parser.parse_args()

    my_test = TestManager(args.serial_number, args.testname)

    try:
        my_test.drive_check(discovery=True)
        if my_test.run():
            my_test.set_final_result()
        my_test.drive_check(discovery=False)
    except Exception as e:
        print(f"ERROR {e}")

if __name__ == "__main__":
    main()
