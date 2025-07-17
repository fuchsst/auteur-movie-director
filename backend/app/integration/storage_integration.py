"""
Storage Integration

Integrates function outputs with the storage service and project structure.
"""

import logging
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import aiohttp
import aiofiles

from .models import StoredFile, OutputContext, Project
from ..services.storage import StorageService
from ..services.git_lfs import git_lfs_service

logger = logging.getLogger(__name__)


class StorageIntegration:
    """Integrate function outputs with storage service"""
    
    def __init__(self):
        self.storage_service = StorageService()
        self.git_lfs_service = git_lfs_service
        self.large_file_threshold = 10 * 1024 * 1024  # 10MB
    
    async def store_function_outputs(self,
                                   outputs: Dict[str, Any],
                                   project: Project,
                                   context: OutputContext) -> Dict[str, StoredFile]:
        """Store function outputs in project structure"""
        
        stored_files = {}
        
        logger.info(f"Storing outputs for task {context.task_id} in project {project.id}")
        
        for output_name, output_data in outputs.items():
            try:
                if self._is_file_output(output_data):
                    stored_file = await self._store_file_output(
                        output_name, output_data, project, context
                    )
                    stored_files[output_name] = stored_file
                    
                    # Track with Git LFS if large
                    if stored_file.size > self.large_file_threshold:
                        await self._track_with_git_lfs(stored_file, project)
                        
                else:
                    # Store as metadata/text
                    stored_file = await self._store_text_output(
                        output_name, output_data, project, context
                    )
                    stored_files[output_name] = stored_file
                    
                logger.debug(f"Stored output {output_name} as {stored_file.path}")
                
            except Exception as e:
                logger.error(f"Failed to store output {output_name}: {e}")
                # Continue with other outputs
        
        logger.info(f"Stored {len(stored_files)} outputs for task {context.task_id}")
        return stored_files
    
    def _is_file_output(self, output_data: Any) -> bool:
        """Check if output represents a file"""
        
        if isinstance(output_data, dict):
            return (
                'type' in output_data and output_data['type'] == 'file'
                or 'url' in output_data
                or 'data' in output_data and 'content_type' in output_data
            )
        elif isinstance(output_data, str):
            # Check if it looks like a file path or URL
            return (
                output_data.startswith(('http://', 'https://'))
                or output_data.startswith('/tmp/')
                or '.' in output_data.split('/')[-1]  # Has file extension
            )
        
        return False
    
    async def _store_file_output(self,
                               output_name: str,
                               output_data: Any,
                               project: Project,
                               context: OutputContext) -> StoredFile:
        """Store a file output"""
        
        # Determine storage path
        storage_path = self._determine_storage_path(
            project, context, output_name, output_data
        )
        
        # Ensure directory exists
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        if isinstance(output_data, dict):
            if 'url' in output_data:
                # Download from URL
                return await self._download_and_store(
                    output_data['url'], storage_path, output_data
                )
            elif 'data' in output_data:
                # Store raw data
                return await self._store_raw_data(
                    output_data['data'], storage_path, output_data
                )
        elif isinstance(output_data, str):
            if output_data.startswith(('http://', 'https://')):
                # Download from URL
                return await self._download_and_store(
                    output_data, storage_path, {'type': 'file'}
                )
            else:
                # Copy local file
                return await self._copy_local_file(
                    output_data, storage_path
                )
        
        raise ValueError(f"Unknown file output format: {output_data}")
    
    async def _store_text_output(self,
                               output_name: str,
                               output_data: Any,
                               project: Project,
                               context: OutputContext) -> StoredFile:
        """Store a text/metadata output"""
        
        # Determine storage path
        storage_path = self._determine_storage_path(
            project, context, f"{output_name}.json", {'type': 'json'}
        )
        
        # Ensure directory exists
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to JSON and store
        import json
        
        async with aiofiles.open(storage_path, 'w') as f:
            await f.write(json.dumps(output_data, indent=2))
        
        # Calculate checksum
        checksum = await self._calculate_checksum(storage_path)
        
        return StoredFile(
            path=str(storage_path),
            relative_path=str(storage_path.relative_to(project.path)),
            size=storage_path.stat().st_size,
            content_type='application/json',
            checksum=checksum,
            metadata={
                'output_name': output_name,
                'task_id': context.task_id,
                'stored_at': context.timestamp
            }
        )
    
    async def _download_and_store(self,
                                url: str,
                                storage_path: Path,
                                metadata: Dict[str, Any]) -> StoredFile:
        """Download file from URL and store"""
        
        logger.debug(f"Downloading {url} to {storage_path}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                
                # Get content info
                content_type = response.headers.get('content-type', 'application/octet-stream')
                content_length = int(response.headers.get('content-length', 0))
                
                # Stream download to file
                async with aiofiles.open(storage_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
        
        # Calculate actual size and checksum
        size = storage_path.stat().st_size
        checksum = await self._calculate_checksum(storage_path)
        
        return StoredFile(
            path=str(storage_path),
            relative_path=str(storage_path.relative_to(storage_path.parents[4])),  # Relative to workspace
            size=size,
            content_type=content_type,
            checksum=checksum,
            metadata={
                'source_url': url,
                'download_time': context.timestamp,
                **metadata
            }
        )
    
    async def _store_raw_data(self,
                            data: Any,
                            storage_path: Path,
                            metadata: Dict[str, Any]) -> StoredFile:
        """Store raw data to file"""
        
        logger.debug(f"Storing raw data to {storage_path}")
        
        if isinstance(data, str):
            # Text data
            async with aiofiles.open(storage_path, 'w') as f:
                await f.write(data)
            content_type = metadata.get('content_type', 'text/plain')
        elif isinstance(data, bytes):
            # Binary data
            async with aiofiles.open(storage_path, 'wb') as f:
                await f.write(data)
            content_type = metadata.get('content_type', 'application/octet-stream')
        else:
            # JSON data
            import json
            async with aiofiles.open(storage_path, 'w') as f:
                await f.write(json.dumps(data, indent=2))
            content_type = 'application/json'
        
        # Calculate size and checksum
        size = storage_path.stat().st_size
        checksum = await self._calculate_checksum(storage_path)
        
        return StoredFile(
            path=str(storage_path),
            relative_path=str(storage_path.relative_to(storage_path.parents[4])),
            size=size,
            content_type=content_type,
            checksum=checksum,
            metadata=metadata
        )
    
    async def _copy_local_file(self,
                             source_path: str,
                             storage_path: Path) -> StoredFile:
        """Copy local file to storage location"""
        
        logger.debug(f"Copying {source_path} to {storage_path}")
        
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        # Copy file
        shutil.copy2(source, storage_path)
        
        # Calculate checksum
        checksum = await self._calculate_checksum(storage_path)
        
        # Determine content type
        content_type = self._guess_content_type(storage_path)
        
        return StoredFile(
            path=str(storage_path),
            relative_path=str(storage_path.relative_to(storage_path.parents[4])),
            size=storage_path.stat().st_size,
            content_type=content_type,
            checksum=checksum,
            metadata={
                'source_path': source_path,
                'copy_time': context.timestamp
            }
        )
    
    def _determine_storage_path(self,
                              project: Project,
                              context: OutputContext,
                              output_name: str,
                              output_data: Any) -> Path:
        """Determine where to store output file"""
        
        project_path = Path(project.path)
        
        # Base path based on context
        if context.shot_id:
            base_path = project_path / "03_Renders" / context.shot_id
        else:
            base_path = project_path / "03_Renders" / "general"
        
        # Add take directory
        take_dir = base_path / f"take_{context.take_number:03d}"
        
        # Determine filename and extension
        if isinstance(output_data, dict) and 'filename' in output_data:
            filename = output_data['filename']
        else:
            # Generate filename
            extension = self._get_file_extension(output_data)
            filename = f"{output_name}_{context.timestamp}{extension}"
        
        return take_dir / filename
    
    def _get_file_extension(self, output_data: Any) -> str:
        """Get appropriate file extension"""
        
        if isinstance(output_data, dict):
            if 'content_type' in output_data:
                content_type = output_data['content_type']
                if content_type.startswith('image/'):
                    return '.png'
                elif content_type.startswith('video/'):
                    return '.mp4'
                elif content_type.startswith('audio/'):
                    return '.wav'
                elif content_type == 'application/json':
                    return '.json'
            
            if 'url' in output_data:
                url_path = Path(output_data['url'])
                if url_path.suffix:
                    return url_path.suffix
        
        elif isinstance(output_data, str):
            if output_data.startswith(('http://', 'https://')):
                url_path = Path(output_data)
                if url_path.suffix:
                    return url_path.suffix
            else:
                path = Path(output_data)
                if path.suffix:
                    return path.suffix
        
        # Default
        return '.bin'
    
    def _guess_content_type(self, file_path: Path) -> str:
        """Guess content type from file extension"""
        
        extension = file_path.suffix.lower()
        
        content_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.mp4': 'video/mp4',
            '.avi': 'video/avi',
            '.mov': 'video/quicktime',
            '.wav': 'audio/wav',
            '.mp3': 'audio/mpeg',
            '.json': 'application/json',
            '.txt': 'text/plain',
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript'
        }
        
        return content_types.get(extension, 'application/octet-stream')
    
    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file"""
        
        hash_md5 = hashlib.md5()
        
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                hash_md5.update(chunk)
        
        return hash_md5.hexdigest()
    
    async def _track_with_git_lfs(self, stored_file: StoredFile, project: Project):
        """Track large file with Git LFS"""
        
        try:
            from pathlib import Path
            project_path = Path(project.path)
            
            self.git_lfs_service.track_file(
                project_path,
                stored_file.relative_path
            )
            
            logger.debug(f"File {stored_file.relative_path} tracked with Git LFS")
            
        except Exception as e:
            logger.error(f"Failed to track file with Git LFS: {e}")
            # Don't raise - LFS tracking failure shouldn't fail storage
    
    async def cleanup_temporary_files(self, outputs: Dict[str, Any]):
        """Clean up temporary files after storage"""
        
        for output_name, output_data in outputs.items():
            try:
                if isinstance(output_data, str) and output_data.startswith('/tmp/'):
                    temp_path = Path(output_data)
                    if temp_path.exists():
                        temp_path.unlink()
                        logger.debug(f"Cleaned up temporary file: {output_data}")
                
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {output_data}: {e}")
    
    async def verify_stored_files(self, stored_files: Dict[str, StoredFile]) -> Dict[str, bool]:
        """Verify that stored files exist and have correct checksums"""
        
        verification_results = {}
        
        for output_name, stored_file in stored_files.items():
            try:
                file_path = Path(stored_file.path)
                
                # Check file exists
                if not file_path.exists():
                    verification_results[output_name] = False
                    continue
                
                # Check size
                actual_size = file_path.stat().st_size
                if actual_size != stored_file.size:
                    logger.warning(f"Size mismatch for {output_name}: expected {stored_file.size}, got {actual_size}")
                    verification_results[output_name] = False
                    continue
                
                # Check checksum
                actual_checksum = await self._calculate_checksum(file_path)
                if actual_checksum != stored_file.checksum:
                    logger.warning(f"Checksum mismatch for {output_name}")
                    verification_results[output_name] = False
                    continue
                
                verification_results[output_name] = True
                
            except Exception as e:
                logger.error(f"Error verifying {output_name}: {e}")
                verification_results[output_name] = False
        
        return verification_results