import sys
import subprocess
from pathlib import Path


def main():
    if len(sys.argv) < 3:
        print("Usage: python run_all.py <policy_module> <results_folder_name>")
        sys.exit(1)

    policy = sys.argv[1]
    results_name = sys.argv[2]

    for i in range(1, 21):
        day = f"day_{i:03d}"
        output_dir = Path("results") / results_name / day
        log_file = output_dir / "log.txt"

        print(f"Running {day}...")

        # Run simulator
        sim_cmd = [
            sys.executable,
            "-m",
            "simulator",
            "--policy",
            policy,
            "--data",
            "data",
            "--day",
            day,
            "--output",
            str(output_dir),
        ]
        sim_result = subprocess.run(sim_cmd)
        if sim_result.returncode != 0:
            print(f"Error: Simulator failed on {day} with exit code {sim_result.returncode}.")
            sys.exit(sim_result.returncode)

        # Run performance monitor
        perf_cmd = [
            sys.executable,
            "-m",
            "solution.performance_monitor",
            "--data",
            "data",
            "--day",
            day,
            "--log",
            str(log_file),
        ]
        perf_result = subprocess.run(perf_cmd)
        if perf_result.returncode != 0:
            print(f"Error: Performance monitor failed on {day} with exit code {perf_result.returncode}.")
            sys.exit(perf_result.returncode)

    print("All days executed successfully!")


if __name__ == "__main__":
    main()