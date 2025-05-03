# !/usr/bin/env python

"""list import/expot filters from registry
"""

"""
  (C) Copyright 2020 Shojiro Fushimi, all rights reserved

  Redistribution and use in source and binary forms, with or
  without modification, are permitted provided that the following
  conditions are met:

   - Redistributions of source code must retain the above
    copyright notice, this list of conditions and the following
    disclaimer.

   - Redistributions in binary form must reproduce the above
    copyright notice, this list of conditions and the following
    disclaimer in the documentation and/or other materials
    provided with the distribution.

  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER ``AS IS''
  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
  FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
  SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE FOR ANY
  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
  OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
  THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
  TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
  OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY
  OF SUCH DAMAGE.
"""

import sys
from argparse import ArgumentParser
from re import compile as re_compile
from functools import reduce
import csv
import xml.etree.ElementTree

DEFAULT_FIELDS = ['DocumentService', 'UIName', 'Flags']
DEFAULT_FLAGS = ['IMPORT', 'EXPORT', 'DEFAULT', 'PREFERRED']
DEFAULT_KEY_FIELD = 'DocumentService'

DEFAULT_TYPE_FIELDS = ['Extensions', 'MediaType']

NS_RE = re_compile(r'\{(.*?)\}') # Modified for JS template literal

def component_data_dict(file_name: str, component_name: str, node_name: str):
    try:
        tree = xml.etree.ElementTree.parse(file_name)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing XML file '{file_name}': {e}", file=sys.stderr)
        return {}

    namespace_mo = NS_RE.match(root.tag)
    if namespace_mo is None:
        print(f"Warning: Could not find namespace in root tag of '{file_name}'.", file=sys.stderr)
        return {} # Or handle differently if needed

    namespace = {'oor': namespace_mo.group(1)}
    data_dict = {}
    oor_name_attr = f'{{{namespace["oor"]}}}name' # Cache attribute name

    try:
        for component_data in root.findall(f'.//oor:component-data[@oor:name="{component_name}"]', namespace):
            component_node = component_data.find(f'node[@oor:name="{node_name}"]', namespace)
            if component_node is None:
                continue

            for data_node in component_node.findall('node'):
                name = data_node.attrib.get(oor_name_attr)
                if name is None:
                    continue
                prop_dict = {}
                for prop in data_node.findall('prop'):
                    prop_name = prop.attrib.get(oor_name_attr)
                    if prop_name is None:
                        continue
                    value_node = prop.find('value')
                    value_text = value_node.text if value_node is not None else None
                    prop_dict[prop_name] = value_text
                data_dict[name] = prop_dict
    except Exception as e:
        print(f"Error processing XML structure in '{file_name}': {e}", file=sys.stderr)
        # Decide whether to return partial data or empty dict
        return {}
    return data_dict


def main(argv):
    aparser = ArgumentParser(description="List import/export filters from LibreOffice/OpenOffice registry XML files.")
    aparser.add_argument('files', nargs='*', help="Path to registry XML file(s) (e.g., registrymodifications.xcu)")
    aparser.add_argument('--out', '-o', dest='out', action='store', default=None, help="Output CSV file path (default: standard output)")
    aparser.add_argument('--fields', dest='fields', action='store', default=','.join(DEFAULT_FIELDS), help=f"Comma-separated fields to include for filters (default: {','.join(DEFAULT_FIELDS)})")
    aparser.add_argument('--flags', dest='flags', action='store', default=','.join(DEFAULT_FLAGS), help=f"Comma-separated flags to filter (default: {','.join(DEFAULT_FLAGS)})")
    aparser.add_argument('--all-fields', dest='all_fields', action='store_true', default=False, help="Include all available fields for filters")
    aparser.add_argument('--all-flags', dest='all_flags', action='store_true', default=False, help="Show all flags without filtering")
    aparser.add_argument('--key-field', dest='key_field', action='store', default=DEFAULT_KEY_FIELD, help=f"Field to use for sorting (default: {DEFAULT_KEY_FIELD})")
    aparser.add_argument('--show-type-fields', dest='show_type_fields', action='store_true', default=False, help="Include fields from the 'Types' component data")
    aparser.add_argument('--type-fields', dest='type_fields', action='store', default=','.join(DEFAULT_TYPE_FIELDS), help=f"Comma-separated fields to include for types (default: {','.join(DEFAULT_TYPE_FIELDS)})")
    aparser.add_argument('--all-type-fields', dest='all_type_fields', action='store_true', default=False, help="Include all available fields for types")
    args = aparser.parse_args(argv[1:])

    if not args.files:
        print("Error: No input XML file specified.", file=sys.stderr)
        aparser.print_help()
        return 1

    filter_dict = reduce(lambda x,y:dict(x, **y),
                         (component_data_dict(file_name, 'Filter', 'Filters') for file_name in args.files),
                         {})
    if not filter_dict:
         print("Error: Could not extract any filter data from the provided file(s).", file=sys.stderr)
         return 1

    all_available_fields = sorted(list(reduce(lambda x,y:x|y,
                                              (set(v.keys()) for v in filter_dict.values()),
                                              set())))
    if not all_available_fields:
        print("Warning: No fields found in filter data.", file=sys.stderr)
        fields = []
    elif args.all_fields:
        fields = all_available_fields
    else:
        fields = [f.strip() for f in args.fields.split(',') if f.strip() in all_available_fields]
        if not fields:
             print(f"Warning: Specified fields '{args.fields}' not found in data. Available: {', '.join(all_available_fields)}", file=sys.stderr)
        if args.show_type_fields and 'Type' not in fields and 'Type' in all_available_fields:
            fields.append('Type')

    # Filter flags if necessary
    if 'Flags' in fields and not args.all_flags:
        valid_flags = {f.strip() for f in args.flags.split(',')}
        for d in filter_dict.values():
            if 'Flags' in d and d['Flags']: # Check if 'Flags' exists and is not None/empty
                d['Flags'] = ' '.join([f for f in d['Flags'].split() if f in valid_flags])

    # Handle Type data if requested
    type_dict = {}
    type_fields = []
    if args.show_type_fields:
        type_dict = reduce(lambda x,y:dict(x, **y),
                           (component_data_dict(file_name, 'Types', 'Types') for file_name in args.files),
                           {})
        if type_dict: # Only process if type data was found
            all_available_type_fields = sorted(list(reduce(lambda x,y:x|y,
                                                         (set(v.keys()) for v in type_dict.values()),
                                                         set())))
            if not all_available_type_fields:
                 print("Warning: No fields found in type data.", file=sys.stderr)
            elif args.all_type_fields:
                type_fields = all_available_type_fields
            else:
                type_fields = [f.strip() for f in args.type_fields.split(',') if f.strip() in all_available_type_fields]
                if not type_fields:
                    print(f"Warning: Specified type fields '{args.type_fields}' not found in data. Available: {', '.join(all_available_type_fields)}", file=sys.stderr)
        else:
             print("Warning: Could not extract any type data.", file=sys.stderr)


    # Prepare table header
    head = ['Name'] + fields + type_fields

    # Prepare table data
    table = []
    for k, v in filter_dict.items():
        row_data = [k]
        # Add filter fields
        row_data.extend([v.get(f) for f in fields])
        # Add type fields if applicable
        if args.show_type_fields and 'Type' in v and v['Type'] in type_dict:
            type_info = type_dict[v['Type']]
            row_data.extend([type_info.get(n) for n in type_fields])
        else:
             # Add placeholders if type info is missing or not requested for this row
            row_data.extend([None] * len(type_fields))
        table.append(row_data)


    # Sort table
    try:
        keyidx = head.index(args.key_field)
        # Use a tuple for secondary sort key to ensure stable sort if primary keys are equal
        key = lambda r:(r[keyidx] is None, r[keyidx], r) # Sort None values last
        table = sorted(table, key=key)
    except ValueError:
        print(f"Warning: Key field '{args.key_field}' not found in header. Sorting by 'Name'.", file=sys.stderr)
        key = lambda r:(r[0] is None, r[0], r)
        table = sorted(table, key=key)
    except Exception as e:
        print(f"Error during sorting: {e}", file=sys.stderr)
        # Proceed without sorting or handle error differently

    # Insert header row
    table.insert(0, head)

    # Write CSV output
    try:
        if args.out is not None:
            # Ensure directory exists for output file
            out_dir = os.path.dirname(args.out)
            if out_dir and not os.path.exists(out_dir):
                os.makedirs(out_dir, exist_ok=True)
            with open(args.out, 'w', newline='', encoding='utf-8') as outfp: # Specify encoding
                csv.writer(outfp).writerows(table)
        else:
            # Ensure stdout uses UTF-8 or handle encoding appropriately
            outfp = sys.stdout
            # Consider potential encoding issues when writing to stdout
            try:
                 csv.writer(outfp).writerows(table)
            except UnicodeEncodeError:
                 print("
Error: Could not encode output for stdout. Try redirecting to a file or check terminal encoding.", file=sys.stderr)
                 return 1

    except IOError as e:
        print(f"Error writing output file '{args.out}': {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"An unexpected error occurred during CSV writing: {e}", file=sys.stderr)
        return 1

    return 0

if __name__ == '__main__':
    # Check if running in an environment where sys.argv exists and is usable
    if hasattr(sys, 'argv'):
        rc = main(sys.argv)
        sys.exit(rc)
    else:
        # Handle cases where sys.argv might not be available (e.g., embedded interpreter)
        print("Error: Cannot run as script in this environment (sys.argv not available).", file=sys.stderr)
        sys.exit(1)