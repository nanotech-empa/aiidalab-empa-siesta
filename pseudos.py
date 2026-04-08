import requests
import os
from aiida.plugins import DataFactory
from aiida.orm import Group, QueryBuilder
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Settings ---
PsfData = DataFactory('pseudo.psf')


FAMILY_NAME = "psf_family" 

BASE_URL = "https://nninc.cnf.cornell.edu/psp_files"

def download_and_install_pseudo(element, log_widget=None):
    local_filename = f"{element}.psf"
    
    url_gga = f"{BASE_URL}/{element}-gga.psf"
    url_std = f"{BASE_URL}/{element}.psf"
    
    def log(msg):
        if log_widget:
            with log_widget:
                print(msg)
        else:
            print(msg)

    log(f"Checking Cornell for {element}...")

    try:
        # Attempt 1: Try {element}-gga.psf
        response = requests.get(url_gga, timeout=30, verify=False)
        
        if response.status_code == 200:
            log(f"Found GGA version: {element}-gga.psf")
        else:
            # Attempt 2: Fallback to {element}.psf
            log(f"'{element}-gga.psf' not found. Trying standard '{element}.psf'...")
            response = requests.get(url_std, timeout=30, verify=False)
            
            if response.status_code != 200:
                log(f"Error {response.status_code}: No pseudo found for {element} on Cornell.")
                return None

        if b"<!DOCTYPE html>" in response.content[:20] or b"<html" in response.content[:20]:
            log(f"Error: Server returned a webpage instead of a PSF file.")
            return None

        with open(local_filename, 'wb') as f:
            f.write(response.content)

        with open(local_filename, 'rb') as stream:
            try:
                pseudo = PsfData(stream, filename=local_filename)
            except Exception as e:
                log(f"Invalid PSF file content: {e}")
                return None

            qb = QueryBuilder()
            qb.append(PsfData, filters={'attributes.md5': pseudo.md5})
            existing = qb.first()
            
            if existing:
                final_node = existing[0]
                log(f"{element}: Already installed (PK: {final_node.pk}).")
            else:
                pseudo.store()
                final_node = pseudo
                log(f"{element}: Downloaded & Stored.")

        # Add to Group (psf_family)
        group, _ = Group.objects.get_or_create(label=FAMILY_NAME)
        if final_node.pk not in [n.pk for n in group.nodes]:
            group.add_nodes([final_node])
            log(f"Added to family '{FAMILY_NAME}'")
        
        return final_node

    except Exception as e:
        log(f"Critical Error: {e}")
        return None
    finally:
        if os.path.exists(local_filename):
            os.remove(local_filename)