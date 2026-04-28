# Comment out what you don't want to run, and uncomment what you do want to run. The numbers are the project IDs in the dataset, which you can find in the paper.
# Make sure to have the correct docker images built,
# dynamic linter, no coverage
# for i in 1 12 23 31 36 37; do
#   bash run_single_project.sh $i nocov
# done

# dynamic linter, with analysis coverage
for i in 1 12 23; do #  31 36 37
  bash run_single_project.sh $i cov
done

# plain test-suite coverage
for i in 1 12 23; do #  31 36 37
  bash run_single_testcov.sh $i
done

# static linter
for i in 1 12 23; do #  31 36 37
  bash run_single_linter.sh $i
done