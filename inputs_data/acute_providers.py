"""Get Acute Providers"""

from functools import cache

import pyspark.sql.functions as F
from pyspark.context import SparkContext
from pyspark.sql import DataFrame


@cache
def get_acute_providers(spark: SparkContext) -> DataFrame:
    """Get Acute Providers

    get the list of acute providers

    :param spark: The spark context to use
    :type spark: SparkContext
    :return: data frame of acute providers
    :rtype: DataFrame
    """
    acute_df = (
        spark.read.table("strategyunit.reference.ods_trusts")
        .filter(F.col("org_type").startswith("ACUTE"))
        .persist()
    )

    return acute_df


def _filter_acute_providers(
    df: DataFrame, spark: SparkContext, org_code_col: str = "provider"
) -> DataFrame:
    """Filter a data frame to the acute providers

    :param df: the data frame to filter
    :type df: DataFrame
    :param spark: The spark context to use
    :type spark: SparkContext
    :param org_code_col: the org code column
    :type org_code_col: str
    :return: _description_
    :rtype: DataFrame
    """
    acute_df = (
        get_acute_providers(spark)
        .select(F.col("org_to").alias(org_code_col))
        .distinct()
    )

    return df.join(acute_df, org_code_col, "semi")


DataFrame.filter_acute_providers = _filter_acute_providers
