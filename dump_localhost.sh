#!/usr/bin/bash

pg_dump --dbname=postgres --file="/Users/ixtli/Downloads/first.sql" --data-only --schema='monday' --table=monday.acceptedpayorcomment --table=monday.address --table=monday.credential --table=monday.degree --table=monday.directory --table=monday.group --table=monday.language --table=monday.license --table=monday.licensor --table=monday.modality --table=monday.orientation --table=monday."payment_method" --table=monday.payor --table=monday.phone --table=monday."phones_addresses" --table=monday.plan --table=monday.provider --table=monday.specialty

pg_dump --dbname=postgres --file="/Users/ixtli/Downloads/secondary.sql" --data-only --schema='monday' --table=monday."providers_acceptedpayorcomments" --table=monday."providers_addresses" --table=monday."providers_credentials" --table=monday."providers_degrees" --table=monday."providers_directories" --table=monday."providers_groups" --table=monday."providers_languages" --table=monday."providers_modalities" --table=monday."providers_orientations" --table=monday."providers_payment_methods" --table=monday."providers_phones" --table=monday."providers_plans" --table=monday."providers_specialties"


