test_that("analysis R package placeholder loads", {
  # PENDING (MB-00): R toolchain not yet confirmed by Bharg. Remove skip() once confirmed.
  skip("R toolchain pending confirmation")
  source("../../R/placeholder.R")
  expect_equal(mindbench_name(), "mindbench")
})
